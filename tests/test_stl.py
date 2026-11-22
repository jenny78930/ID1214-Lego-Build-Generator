from legogen.stl import stl_bounds

TRIANGLE = """solid t
facet normal 0 0 1
 outer loop
  vertex 0 0 0
  vertex 4 0 0
  vertex 0 3 2
 endloop
endfacet
endsolid t
"""


def test_bounds(tmp_path):
    path = tmp_path / "a.stl"
    path.write_text(TRIANGLE)
    assert stl_bounds(path) == ((0, 0, 0), (4, 3, 2))


def test_empty_file_has_no_bounds(tmp_path):
    path = tmp_path / "e.stl"
    path.write_text("solid OpenSCAD_Model\nendsolid OpenSCAD_Model\n")
    assert stl_bounds(path) is None
