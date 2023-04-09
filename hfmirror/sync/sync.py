import json
import os.path
from typing import List, Tuple

from hbutils.reflection import nested_with
from hbutils.string import plural_word
from hbutils.system.filesystem.tempfile import TemporaryDirectory
from tqdm import tqdm as _TqdmType
from tqdm.auto import tqdm

from ..resource import SyncResource, SyncTree, ResourceNotChange
from ..storage import BaseStorage


def _count_trees(tree: SyncTree):
    tree_cnt, file_cnt = 1, 0
    for _, item in tree.items.items():
        if isinstance(item, SyncTree):
            l_tree_cnt, l_file_cnt = _count_trees(item)
            tree_cnt += l_tree_cnt
            file_cnt += l_file_cnt
        else:
            file_cnt += 1

    return tree_cnt, file_cnt


class SyncTask:
    __meta_filename__ = '.meta.json'

    def __init__(self, resource: SyncResource, storage: BaseStorage):
        self.resource = resource
        self.storage = storage

    def _sync_tree(self, tree: SyncTree, segments: List[str], tqdms: Tuple[_TqdmType, _TqdmType]):
        tree_tqdm, file_tqdm = tqdms
        tree_tqdm.set_description('/'.join(segments))
        items, folders = [], []
        for key in sorted(tree.items.keys()):
            value = tree.items[key]
            if isinstance(value, SyncTree):
                folders.append((key, value))
            else:
                items.append((key, value))

        meta_file_segments = [*segments, self.__meta_filename__]
        if self.storage.file_exists(meta_file_segments):
            old_metadata = json.loads(self.storage.read_text(meta_file_segments))
            old_files = {item['name']: item for item in old_metadata['files']}
        else:
            old_files = {}

        m_folders = []
        for key, folder in folders:
            self._sync_tree(folder, [*segments, key], tqdms)
            m_folders.append({'name': key, 'metadata': folder.metadata})

        m_files = []
        need_load_files = []
        for key, item in items:
            old_file_data = old_files.get(key)
            if old_file_data and old_file_data['type'] == item.__type__:
                try:
                    mark = item.refresh_mark(old_file_data['mark'])
                except ResourceNotChange:
                    need_load, mark = False, old_file_data['mark']
                else:
                    need_load = True
            else:
                need_load = True
                mark = item.refresh_mark(None)

            if need_load:
                need_load_files.append((key, item))
            else:
                file_tqdm.update()
                file_tqdm.set_description(plural_word(file_tqdm.n, 'file'))

            m_files.append({
                'name': key,
                'type': item.__type__,
                'mark': mark,
                'metadata': item.metadata,
            })

        with TemporaryDirectory() as td:
            local_metafile = os.path.join(td, self.__meta_filename__)
            with open(local_metafile, 'w') as f:
                json.dump({
                    'path': '/'.join(segments),
                    'metadata': tree.metadata,
                    'files': m_files,
                    'folders': m_folders,
                }, f, indent=4, ensure_ascii=False)

            with nested_with(*[item.load_file() for _, item in need_load_files]) as file_paths:
                changes = [(local_metafile, [*segments, self.__meta_filename__])]
                for local_file, (key, _) in zip(file_paths, need_load_files):
                    changes.append((local_file, [*segments, key]))

                self.storage.batch_change_files(changes)

            file_tqdm.update(len(need_load_files))
            file_tqdm.set_description(plural_word(file_tqdm.n, 'file'))

        tree_tqdm.update()

    def sync(self):
        tree: SyncTree = self.resource.sync_tree()
        total_trees, total_files = _count_trees(tree)
        tree_tqdm = tqdm(total=total_trees)
        file_tqdm = tqdm(total=total_files)
        self._sync_tree(tree, [], (tree_tqdm, file_tqdm))
