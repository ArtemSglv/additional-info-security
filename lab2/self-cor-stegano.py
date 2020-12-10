import io
import sys

from PIL import Image, ImageDraw

import lab2.AESCrypto as aes
import lab2.utils as utils


def expand_image(img, small_image, fragment_size):
    factor = 2
    # small_image.show()
    img_width, img_height = img.size
    px = small_image.load()
    width, height = small_image.size

    img = Image.new('RGB', (width * factor + 2, height * factor + 2), 'Black')
    pixels = img.load()
    for i in range(width):
        for j in range(height):
            pixels[factor * i, factor * j] = px[i, j]
            pixels[factor * i + 1, factor * j] = px[i, j]
            pixels[factor * i + 2, factor * j] = px[i, j]

            pixels[factor * i, factor * j + 1] = px[i, j]
            pixels[factor * i + 1, factor * j + 1] = px[i, j]
            pixels[factor * i + 2, factor * j + 1] = px[i, j]

            pixels[factor * i, factor * j + 2] = px[i, j]
            pixels[factor * i + 1, factor * j + 2] = px[i, j]
            pixels[factor * i + 2, factor * j + 2] = px[i, j]
    img = img.crop((0, 0, img_width * fragment_size, img_height * fragment_size))
    # img.show()
    # img.save("expand_image.jpg", "JPEG")
    return img


def steganography_process(img, encrypted_fragment, fragment_size):
    conv = img.convert("RGBA").getdata()
    width, height = img.size
    max_size = width * height * 3.0 / 8 / 1024

    v = utils.decompose(encrypted_fragment)
    while len(v) % 3:
        v.append(0)

    payload_size = len(v) / 8 / 1024.0
    print("Encrypted payload size: %.3f KB " % payload_size)
    print("Max payload size: %.3f KB " % max_size)
    print("Коэффициент эффективного использования: %.3f " % float(
        100 * fragment_size**2))
    if payload_size > max_size - 4:
        print("Cannot embed. File too large")
        sys.exit()

    steg_img = Image.new('RGBA', (width, height))
    data_img = steg_img.getdata()

    idx = 0
    for h in range(height):
        for w in range(width):
            (r, g, b, a) = conv.getpixel((w, h))
            if idx < len(v):
                r = utils.set_bit(r, 0, v[idx])
                g = utils.set_bit(g, 0, v[idx + 1])
                b = utils.set_bit(b, 0, v[idx + 2])
            data_img.putpixel((w, h), (r, g, b, a))
            idx = idx + 3

    steg_img.save("steg_img.png", "PNG")
    # print("stegano img")
    # steg_img.show()
    return steg_img


def compose_image(img, dec_fragment, fragment_size):
    image_stream = io.BytesIO(dec_fragment)
    fragment = Image.open(image_stream)
    fragment.show()

    width, height = img.size
    fragment = expand_image(img, fragment, fragment_size)
    f_width, f_height = fragment.size

    x_start = int((width - f_width) / 2)
    y_start = int((height - f_height) / 2)

    final_img = img.copy()
    position = (x_start, y_start)
    final_img.paste(fragment, position)
    # img_copy.save('pasted_image.jpg')
    # img_copy.show()

    return final_img


def encrypt_data(crypto_key, image_data):
    buf = io.BytesIO()
    image_data.save(buf, format='JPEG')
    byte_im = buf.getvalue()

    encrypted_data = aes.encrypt_image(byte_im, crypto_key)

    # сохраняем зашифрованное изображение
    with open("data.enc", 'wb') as fo:
        fo.write(encrypted_data)

    return encrypted_data


def decrypt_data(key, enc_data):
    decrypted_data = aes.decrypt_image(enc_data, key)
    # сохраняем дешифрованную информацию
    with open("data.dec", 'wb') as fo:
        fo.write(decrypted_data)

    return decrypted_data


def get_fragment_image(img, fragment_size):
    #  Шаг 1: выбор фрагмента
    # размер фрагмента(сколько процентов изображения скрыть)
    width, height = img.size
    fragment_width = int(width * fragment_size)
    fragment_height = int(height * fragment_size)

    # координаты фрагмента
    x_start = int((width - fragment_width) / 2)
    y_start = int((height - fragment_height) / 2)
    x_stop = x_start + fragment_width
    y_stop = y_start + fragment_height

    # берем фрагмент
    fragment_image = image.crop((x_start, y_start, x_stop, y_stop))
    print("fragment img")
    # fragment_image.show()

    # Шаг 2: искажение объекта
    draw = ImageDraw.Draw(img)
    for x in range(x_start, x_stop):
        for y in range(y_start, y_stop):
            draw.point((x, y), (0, 0, 0))
    # искаженное изображение
    print("censored img")
    img.show()

    # Шаг 3: сжатие объекта
    max_size = (fragment_width / 2, fragment_height / 2)
    fragment_image.thumbnail(max_size, Image.ANTIALIAS)
    print("compressed fragment")
    # fragment_image.show()

    return fragment_image


if __name__ == '__main__':
    # оригинальное изображение
    image = Image.open("./tiger_original.jpg")
    print("original img")
    # image.show()
    # криптографический ключ
    password = "test_pass"
    password2 = "wrong_pass"

    fragment_size = .7

    compressed_fragment = get_fragment_image(image, fragment_size=fragment_size)

    key_pbkdf2 = aes.get_key_pbkdf2(password)

    encrypted_fragment = encrypt_data(key_pbkdf2, compressed_fragment)

    steg_image = steganography_process(image, encrypted_fragment, fragment_size=fragment_size)

    ###################

    extracting_data = utils.extract(steg_image)
    # дешифруем
    # key_pbkdf2 = aes.get_key_pbkdf2(password2)
    decrypted_fragment = decrypt_data(key_pbkdf2, extracting_data)
    # получаем картинку из дешифрованного фрагмента
    composed_image = compose_image(image, decrypted_fragment, fragment_size=fragment_size)
    print("final img")
    composed_image.show()
