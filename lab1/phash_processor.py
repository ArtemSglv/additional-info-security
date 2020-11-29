import math

import image_slicer
from PIL import Image
from stegano import lsb

from lab1.imagehash import phash_simple


def hamming_distance(str1, str2):
    dist = 0
    for i in range(len(str1)):
        if str1[i] != str2[i]:
            dist += 1
    return dist


def find_diff(original_filepath, deformed_filepath):
    with Image.open(original_filepath) as img:
        w, h = img.size
    hash_length = 64
    block_size = 16
    col = math.ceil(w / block_size)
    row = math.ceil(h / block_size)
    threshold = hash_length * 0.15

    original_tiles = image_slicer.slice(original_filepath, col=col, row=row, save=False)
    deformed_tiles = image_slicer.slice(deformed_filepath, col=col, row=row, save=False)

    for original_tile, deformed_tile in zip(original_tiles, deformed_tiles):
        original_tile.image = lsb.hide(original_tile.image, str(phash_simple(original_tile.image)))
        deformed_tile.image = lsb.hide(deformed_tile.image, str(phash_simple(deformed_tile.image)))

        decoded_hash1 = lsb.reveal(original_tile.image.copy())
        decoded_hash2 = lsb.reveal(deformed_tile.image.copy())

        if hamming_distance(decoded_hash1, decoded_hash2) > threshold:
            deformed_tile.image = deformed_tile.image.convert("RGB", (1, 0, 0, 0,
                                                                      0, 0, 0, 0,
                                                                      0, 0, 1, 0))

    result_img = image_slicer.join(deformed_tiles)
    result_img.save("result.png")
    result_img.show()


if __name__ == "__main__":
    original_img = 'tiger_original.jpg'
    changed_img = 'tiger_changed.jpg'
    find_diff(original_img, changed_img)
