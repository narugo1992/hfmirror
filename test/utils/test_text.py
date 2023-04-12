import pytest

from hfmirror.utils import text_concat, text_parallel, cycle


@pytest.mark.unittest
class TestUtilsText:
    def test_text_concat(self, text_align):
        text_align.assert_equal(text_concat('a', '[metadata]\n\n\nt', 'f: 1\nt: 2222'), """
            a
            [metadata]
            
            
            t
            f: 1
            t: 2222
        """)

    def test_text_parallel(self, text_align):
        text_align.assert_equal(text_parallel(), '')

        a = "a\nnihao\n\n   what th e f"
        b = " skdf sdf\nsdkfhkjsd sdf"
        c = "ks sd f sdf  \r\n sdkf sdf s0d82 \n  sd f sdf \n sdf sdf sd fsd\n\n\n df"

        text_align.assert_equal(
            text_parallel(a, cycle(' - '), b, cycle(' - \n + '), c),
            """
               a              -  skdf sdf     - ks sd f sdf  
               nihao          - sdkfhkjsd sdf +  sdkf sdf s0d82 
                              -               -   sd f sdf 
                  what th e f -               +  sdf sdf sd fsd
                              -               - 
                              -               + 
                              -               -  df
            """
        )

        with pytest.raises(TypeError):
            _ = text_parallel('f', 1, 2)
