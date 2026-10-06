# Task 04 image sources

The normal notebook demonstration downloads one image using `wget`. Its public
URL does not require this project's GitHub login or a Google Drive mount. The
CUDA program processes that one input and saves its X gradient, Y gradient and
combined Sobel edge image. The notebook displays those outputs beside the
original image in four views.

- [download.png](https://i.ibb.co/5gB80K0Z/download.png), 300 x 300: the exact
  image URL in the lecturer's last-class code. The supplied teaching material
  does not identify the image's original author or licence.
The input is stored without resizing or conversion. `public_images.json`
contains only `download.png` and records its URL, dimensions and SHA-256
checksum. It is the only PNG input included in this notebook's resource copy.

Setup downloads this public image again and verifies its checksum and PNG
dimensions. If a public host is unavailable or its bytes change, the notebook
prints that it is using its verified bundled copy. `image_downloads.json` records
which mode was used during that run. The isolated
`/content/HPC_Task_04_OneImage` folder keeps resources from earlier multi-image
notebooks out of the demonstration and checks.

The independent validation cell separately creates thirteen small PNG fixtures
in a temporary directory. They test zero padding, grayscale rounding,
transparent pixels, both gradient directions and the brief's Gx=6, Gy=8,
magnitude=10 example. Together with the single public input, this gives fourteen
input checks and forty-two output-map checks. These fixtures test the program's
multiple-image capability; they are separate from the normal one-image
demonstration. Every test compares both gradient maps and the final edge image
independently.
