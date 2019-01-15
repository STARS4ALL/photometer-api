# coding=utf-8
# -*- coding: utf-8 -*-
from tess.tess import Tess
from tess_grafana import TessGrafana

from config import Configuration
import requests
import base64
import sys

config = None
tess_grafana = None


def init():
    global config
    config = Configuration().config


def update_tess(tess):
    try:
        tess_object = Tess(tess, config.PHOTOMETERS_API_URL).generate_tokens(
            config.SERVER_PROTOCOL + "://" + config.SERVER_HOST, config.PRODUCTION_ORG_ID)
        result = tess_grafana.generate_datasheet(tess_object)
        # print(result)
        result = tess_grafana.add_or_update_tess_in_country_list(tess_object)
        # print(result)
        result = tess_grafana.add_or_update_tess_in_lastet_measures(tess_object)
        # print(result)
        result = tess_grafana.add_or_update_tess_in_comparison(tess_object)
        # print(result)
        result = tess_grafana.add_or_update_tess_in_heatmap(tess_object)
        # print(result)
        result = tess_grafana.add_or_update_tess_in_statistics(tess_object)
        # print(result)
        result = tess_grafana.add_or_update_tess_in_raw(tess_object)
        # print(result)
    except Exception as e:
        print(e.message)
        pass


def sync_all():

    tess_grafana.generate_map(Tess({}).generate_tokens(config.SERVER_PROTOCOL + "://" + config.SERVER_HOST, config.PRODUCTION_ORG_ID))

    # Load All Photometers
    r = requests.post(config.PHOTOMETERS_API_URL + '/photometers_all',
                      json={'token': base64.b64encode("%s:%s" % (config.SERVER_CREDENTIALS_USER, config.SERVER_CREDENTIALS_PWD))})
    all_tess = r.json()

    for tess in all_tess:
        update_tess(tess)


def sync(name, mac):
    # Load All Photometers
    r = requests.get(config.PHOTOMETERS_API_URL + '/photometers/%s/%s' % (name, mac))
    tess = r.json()
    update_tess(tess)


def main():

    if len(sys.argv) > 1:
        if sys.argv[1] == 'sync':
            # print(str({'success':True,'params':sys.argv[1:]}))
            sync_all()
        elif sys.argv[1] == 'add' or sys.argv[1] == 'update':
            if len(sys.argv) > 3:
                # print(str({'success':True,'params':sys.argv[1:]}))
                sync(sys.argv[2], sys.argv[3])
            else:
                print(str({'error': "No valid params for %s option" % sys.argv[1]}))
        else:
            print(str({'error': "%s is not valid param option" % sys.argv[1]}))
    else:
        print(str({'error': "No params"}))


if __name__ == '__main__':
    init()

    if config:

        tess_grafana = TessGrafana(config.SERVER_CREDENTIALS_USER, config.SERVER_CREDENTIALS_PWD,
                                   config.TEMPLATE_ORG_ID, config.PRODUCTION_ORG_ID, config.SERVER_PROTOCOL, config.SERVER_HOST)
        main()
    else:
        print(str({'error': "No config file"}))
