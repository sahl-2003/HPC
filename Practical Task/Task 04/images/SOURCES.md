# Task 04 image sources

The notebook downloads all three demonstration images from public URLs using
`wget`. These URLs do not require this project's GitHub login or a Google Drive
mount. The source C/CUDA computation uses LodePNG and CUDA; OpenCV is only the
source of two input files and is not used to calculate edges.

- [download.png](https://i.ibb.co/5gB80K0Z/download.png), 300 x 300: the exact
  image URL in the lecturer's last-class code. The supplied teaching material
  does not identify the image's original author or licence.
- [smarties.png](https://raw.githubusercontent.com/opencv/opencv/53ebe537da128f7b4bafed2b524f21baa092f297/samples/data/smarties.png),
  413 x 356: OpenCV sample image.
- [sudoku.png](https://raw.githubusercontent.com/opencv/opencv/53ebe537da128f7b4bafed2b524f21baa092f297/samples/data/sudoku.png),
  558 x 563: OpenCV sample image.

The OpenCV URLs are pinned to revision
`53ebe537da128f7b4bafed2b524f21baa092f297`. Its upstream licence is retained in
`OpenCV_LICENSE.txt`. Original images are stored without resizing or conversion.
`public_images.json` records the URLs, dimensions and SHA-256 checksums.

Setup downloads each public image again and verifies its checksum and PNG
dimensions. If a public host is unavailable or its bytes change, the notebook
prints that it is using its verified bundled copy. `image_downloads.json` records
which mode was used for each image during that run.

The original `shapes.png`, `gradient.png` and `checkerboard.png` files are synthetic
correctness fixtures. They are included in the notebook's resource copy so that
another device can run the same tests while the project repository is private.
They are checked alongside eight small generated fixtures, including the
lecturer's grayscale rounding cases and transparent pixels.
