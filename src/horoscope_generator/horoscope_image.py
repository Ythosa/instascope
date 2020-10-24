import os
import re
from collections import namedtuple
from random import randint, choice
from textwrap import wrap
from urllib.request import urlopen

import requests
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
from saya import Vk

from src.config import config
from src.horoscope_generator.horoscope import Horoscope
from src.horoscope_generator.horoscope_list import HoroscopeList

TITLE_FONT = ImageFont.truetype(config.FONT_PATH, 128)
FONT = ImageFont.truetype(config.FONT_PATH, 32 + 16)


class HoroscopeImageCreator:
    public_page = namedtuple('public', ['owner_id', 'album_id'])
    public_pages = [
        # List albums of memes
        public_page(-45745333, '262436923'),
        public_page(-45745333, '262436923'),
        public_page(-176864224, 'wall'),
        public_page(-29606875, 'wall'),
        public_page(-144918406, 'wall')
    ]

    def __init__(self, horoscope_list: HoroscopeList):
        self.horoscope_list = horoscope_list

    def create(self, name="pic.png", sign="libra"):
        # Parse content
        (title, description) = self.get_horoscope(sign, config.HOROSCOPE_GENERATOR_URL)

        meme_path = 'meme.png'
        self._get_meme(meme_path)

        # params
        width, height = 1080, 1920
        meme_size = 900
        formatted_description = "\n".join(wrap(description, 41))
        start_height = 180

        back = Image.new("RGBA", (width, height), color="#282a36")
        meme = Image.open(meme_path).resize((meme_size, meme_size))
        draw = ImageDraw.Draw(back)

        # title
        w, h = draw.textsize(title, font=TITLE_FONT)
        draw.text(
            (width // 2 - w // 2, start_height),
            title, font=TITLE_FONT, fill="#f8f8f2")

        # description
        w1, h1 = draw.multiline_textsize(formatted_description, font=FONT)
        draw.multiline_text(
            (width // 2 - w1 // 2, start_height + h + (470 - h1) // 2),
            formatted_description, font=FONT, fill="#f8f8f2", align="center")
        back.paste(meme, (90, 930))
        back.save(name)
        if name != meme_path:
            os.remove(meme_path)

    def _get_meme(self, meme_path: str):
        """
        Gets random picture from random public page and writes it in the file.
        """
        choiced_public = choice(self.public_pages)
        vk = Vk(token=config.VK_TOKEN)
        photos = vk.photos.get(  # Gets all photos from album
            owner_id=choiced_public.owner_id, album_id=choiced_public.album_id,
            rev=randint(0, 1), offset=randint(0, 500), count=1000)
        photo = choice(photos["response"]["items"])  # Gets random photo from photos list.
        w = h = 0
        url = ""
        for size in photo["sizes"]:  # Gets max photo size.
            if size["width"] > w and size["height"] > h:
                w = size["width"]
                h = size["height"]
                url = size["url"]
        if url:
            # Write photo in file, if available.
            content = None
            while not content:
                try:
                    content = requests.get(url).content
                except requests.exceptions.ConnectionError:
                    continue
            with open(meme_path, "wb") as f:
                f.write(content)

    def get_horoscope(self, sign, url) -> Horoscope:
        if not self.horoscope_list.is_contains(sign):
            raise ValueError("passed symbol must be one of horoscope symbols")

        html_doc = urlopen(url + sign).read()
        soup = BeautifulSoup(html_doc, features="html.parser")
        soup = str(soup.find('p'))[3:-4]

        horoscope = "".join(re.split(r"([!?.]+)", soup, 3)[:4])

        sign = self.horoscope_list.get_ru_translate_of_sign(sign)

        return Horoscope(str(sign).capitalize(), horoscope)