import os

import requests
from tqdm.auto import tqdm


def file_download(url, filename, expected_size: int = None):
    response = requests.get(url, stream=True, allow_redirects=True)
    response.raise_for_status()
    expected_size = expected_size or response.headers.get('Content-Length', None)
    expected_size = int(expected_size) if expected_size is not None else expected_size

    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(filename, 'wb') as f:
        with tqdm(total=expected_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                pbar.update(len(chunk))

    if expected_size is not None and os.path.getsize(filename) != expected_size:
        os.remove(filename)
        raise requests.exceptions.HTTPError(f"Downloaded file is not of expected size, "
                                            f"{expected_size} expected but {os.path.getsize(filename)} found.")

    return filename
