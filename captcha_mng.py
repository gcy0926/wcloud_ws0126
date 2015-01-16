# -*- coding: utf8 -*-
#!/usr/bin/env python


import logging

from wheezy.captcha.image import captcha
from wheezy.captcha.image import background
from wheezy.captcha.image import curve
from wheezy.captcha.image import noise
from wheezy.captcha.image import smooth
from wheezy.captcha.image import text
from wheezy.captcha.image import offset
from wheezy.captcha.image import rotate
from wheezy.captcha.image import warp

import captcha_db
import config

import os
ttf_path = os.path.dirname(os.path.abspath(__file__))


def get_captcha():
    """
    get a new captcha, will return captcha id and img
    """
    import md5
    value, img_data = new_captcha()
    if not value:
        return '',''
    cid = md5.new(img_data).hexdigest()
    captcha_db.add( cid, value)
    return cid, img_data


def check_captcha( cid, value):
    if value == captcha_db.getandrm(cid):
        return True
    return False


def new_captcha():
    import random
    import string
    import StringIO
    value = ''
    img_date = ''
    try:
        captcha_image = captcha(drawings=[
            background('#fcf7e2'),
            text(fonts=[os.path.join( ttf_path,'ttf','OsakaMono.ttf')],
                font_sizes=(40,45,50),
                drawings=[
                    warp(),
                    rotate(),
                    offset()
                ],
                color='#4e97c7'
                ),
            curve('#4e97c7',width=0, number=2),
            noise(number=0),
            smooth()], 
            width=112, height=38)

        value = ''.join(random.sample(string.uppercase + string.digits, 4))
        image = captcha_image(value)
        img_file = StringIO.StringIO()
        image.save( img_file, 'jpeg', quality=80)
        img_file.seek(0)
        img_date = img_file.read()

    except Exception,ex:
        logging.exception('create captcha img failed.')

    return value, img_date

