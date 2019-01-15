# coding: utf-8
from .location import Location
import re

class Tess:
    # tess = {
    #     "name": "stars201",
    #     "info_location": {
    #         "country": "Spain",
    #         "region": "Extremadura",
    #         "sub_region": "Badajoz",
    #         "town": "Llanos de Olivenza",
    #         "place": "Albergue La Cocosa",
    #         "latitude": 38.7555,
    #         "longitude": -6.9845
    #     },
    #     "info_org": {
    #         "name": "Extremadura, buenas noches",
    #         "logo_url": "https://extremadurabuenasnoches.com/web.png",
    #         "description": "bla bla bla",
    #         "web_url": "https://extremadurabuenasnoches.com/",
    #         "phone": "(+34) 924 00 34 13",
    #         "mail": "proy.transversales@juntaex.es"
    #     },
    #     "info_tess": {
    #         "period": 60
    #     },
    #     "info_contact": {
    #         "mail": "Email de contacto para problemas con el TESS",
    #         "phone": "Telefono de contacto para problemas con el TESS"
    #     },
    #     "info_img":{
    #           "urls": [
    #               "http://www.sky-live.tv/liveimages/webcam/opensky/cam36-mirador2Cocosa-EXT.jpg"
    #           ]
    #     }
    # }

    def __init__(self, tess, api_url=None):
        self.tess = tess
        self.api_url = api_url
        if "name" not in self.tess:
            self.tess["name"] = ""

        if "info_org" not in self.tess or not self.tess["info_org"]:
            self.tess["info_org"] = {}

        if "info_location" not in self.tess or not self.tess["info_location"]:
            self.tess["info_location"] = {}

        if "info_contact" not in self.tess or not self.tess["info_contact"]:
            self.tess["info_contact"] = {}

        if "info_tess" not in self.tess or not self.tess["info_tess"]:
            self.tess["info_tess"] = {}

        if "info_img" not in self.tess or not self.tess["info_img"]:
            self.tess["info_img"] = {"urls": []}

        if "latitude" not in self.tess["info_location"] and "latitude" in self.tess:
            self.tess["info_location"]["latitude"] = self.tess["latitude"]

        if "longitude" not in self.tess["info_location"] and "longitude" in self.tess:
            self.tess["info_location"]["longitude"] = self.tess["longitude"]

        if "place" not in self.tess["info_location"] and "place" in self.tess:
            self.tess["info_location"]["place"] = self.tess["place"]

        # if "town" not in self.tess["info_location"] and "city" in self.tess:
        #     self.tess["info_location"]["town"] = self.tess["city"]

    def __generate_css_tokens(self):
        tokens = {
            "[token_tess_css_org_logo_and_website_display]": "none",
            "[token_tess_css_org_logo_and_website_display_invert]": "visible",
            "[token_tess_css_org_logo_display]": "none",
            "[token_tess_css_org_website_display]": "none",
            "[token_tess_css_org_website_display_invert]": "none",
            "[token_tess_css_org_phone_display]": "none",
            "[token_tess_css_org_email_display]": "none"
        }

        if "info_org" in self.tess:

            if "logo_url" in self.tess["info_org"] and "web_url" in self.tess["info_org"]:
                tokens["[token_tess_css_org_logo_and_website_display]"] = "visible"
                tokens["[token_tess_css_org_logo_and_website_display_invert]"] = "none"

            if "logo_url" in self.tess["info_org"]:
                tokens["[token_tess_css_org_logo_display]"] = "visible"
            else:
                tokens["[token_tess_css_org_logo_display]"] = "none"

            if "web_url" in self.tess["info_org"]:
                tokens["[token_tess_css_org_website_display]"] = "visible"
                tokens["[token_tess_css_org_website_display_invert]"] = "none"
            else:
                tokens["[token_tess_css_org_website_display]"] = "none"
                tokens["[token_tess_css_org_website_display_invert]"] = "visible"

            if "phone" in self.tess["info_org"]:
                tokens["[token_tess_css_org_phone_display]"] = "visible"
            else:
                tokens["[token_tess_css_org_phone_display]"] = "none"

            if "mail" in self.tess["info_org"]:
                tokens["[token_tess_css_org_email_display]"] = "visible"
            else:
                tokens["[token_tess_css_org_email_display]"] = "none"

            if "name" not in self.tess["info_org"]:
                tokens["[token_tess_css_org_website_display]"] = "none"
                tokens["[token_tess_css_org_website_display_invert]"] = "none"

        return tokens

    def __generate_tess_location_tokens(self):
        tokens = {
            "[token_tess_location_country]": "",
            "[token_tess_location_region]": "",
            "[token_tess_location_sub_region]": "",
            "[token_tess_location_town]": "",
            "[token_tess_location_place]": "",
            "[token_tess_location_lat]"	: "",
            "[token_tess_location_lon]": "",
            "[token_tess_openstreetmap_node_url]"	: "",
            "[token_tess_location_region_country]": "",
            "[token_tess_location_regions_country]": "",
            "[token_tess_location_full]": "",
            "[token_tess_location_place_country]": "",
            "[token_tess_location_tags]"	: ""
        }

        region_country = []
        regions_country = []
        full = []
        place_country = []
        tags = []

        if "info_location" in self.tess:

            if "place" in self.tess["info_location"]:
                tokens["[token_tess_location_place]"] = self.tess["info_location"]["place"]

                full.append(self.tess["info_location"]["place"])
                place_country.append(self.tess["info_location"]["place"])
                tags.append(self.tess["info_location"]["place"])

            if "town" in self.tess["info_location"]:
                tokens["[token_tess_location_town]"] = self.tess["info_location"]["town"]

                full.append(self.tess["info_location"]["town"])

            if "sub_region" in self.tess["info_location"]:
                tokens["[token_tess_location_sub_region]"] = self.tess["info_location"]["sub_region"]

                full.append(self.tess["info_location"]["sub_region"])
                regions_country.append(self.tess["info_location"]["sub_region"])
                region_country.append(self.tess["info_location"]["sub_region"])

            if "region" in self.tess["info_location"]:
                tokens["[token_tess_location_region]"] = self.tess["info_location"]["region"]

                full.append(self.tess["info_location"]["region"])
                tags.append(self.tess["info_location"]["region"])
                regions_country.append(self.tess["info_location"]["region"])
                region_country.append(self.tess["info_location"]["region"])

            if "country" in self.tess["info_location"]:
                tokens["[token_tess_location_country]"] = self.tess["info_location"]["country"]

                full.append(self.tess["info_location"]["country"])
                place_country.append(self.tess["info_location"]["country"])
                tags.append(self.tess["info_location"]["country"])
                regions_country.append(self.tess["info_location"]["country"])

            if "latitude" in self.tess["info_location"]:
                tokens["[token_tess_location_lat]"] = self.tess["info_location"]["latitude"]

            if "longitude" in self.tess["info_location"]:
                tokens["[token_tess_location_lon]"] = self.tess["info_location"]["longitude"]

            if "openstreetmap_node" in self.tess["info_location"]:
                tokens["[token_tess_openstreetmap_node_url]"] = "https://www.openstreetmap.org/node/" + \
                    str(self.tess["info_location"]["openstreetmap_node"])

        tokens["[token_tess_location_region_country]"] = ", ".join(region_country)
        tokens["[token_tess_location_regions_country]"] = ", ".join(regions_country)
        tokens["[token_tess_location_full]"] = ", ".join(full)
        tokens["[token_tess_location_place_country]"] = ", ".join(place_country)
        tokens["[token_tess_location_tags]"] = "\",\"".join(tags)

        return tokens

    def __generate_tess_org_tokens(self):
        tokens = {
            "[token_tess_org_name]": "",
            "[token_tess_org_logo_url]": "",
            "[token_tess_org_description]": "",
            "[token_tess_org_web_url]": "",
            "[token_tess_org_contact_phone]": "",
            "[token_tess_org_contact_mail]"	: ""
        }

        if "info_org" in self.tess:
            if "name" in self.tess["info_org"]:
                tokens["[token_tess_org_name]"] = self.tess["info_org"]["name"]

            if "logo_url" in self.tess["info_org"]:
                tokens["[token_tess_org_logo_url]"] = self.tess["info_org"]["logo_url"]

            if "description" in self.tess["info_org"]:
                tokens["[token_tess_org_description]"] = self.tess["info_org"]["description"].replace('\n', '<br>').replace('\r', '')

            if "web_url" in self.tess["info_org"]:
                tokens["[token_tess_org_web_url]"] = self.tess["info_org"]["web_url"]

            if "phone" in self.tess["info_org"]:
                tokens["[token_tess_org_contact_phone]"] = self.tess["info_org"]["phone"]

            if "mail" in self.tess["info_org"]:
                tokens["[token_tess_org_contact_mail]"] = self.tess["info_org"]["mail"]

        return tokens

    def __generate_tess_contact_tokens(self):
        tokens = {
            "[token_tess_contact_mail]": "",
            "[token_tess_contact_phone]": ""
        }

        if "info_contact" in self.tess:

            if "phone" in self.tess["info_contact"]:
                tokens["[token_tess_contact_phone]"] = self.tess["info_contact"]["phone"]

            if "mail" in self.tess["info_contact"]:
                tokens["[token_tess_contact_mail]"] = self.tess["info_contact"]["mail"]

        return tokens

    def __generate_tess_tokens(self):
        tokens = {
            "[token_tess_total_day_meditions]": 24 * 60,
            "[token_tess_period_seconds]": 60,
            "[token_tess_repository_url]": "https://delicias.dia.fi.upm.es/nextcloud/index.php/s/VeU1YVuzK16hpls?path=" + (self.tess["name"])
        }

        if "info_tess" in self.tess:
            if "period" in self.tess["info_tess"]:
                tokens["[token_tess_total_day_meditions]"] = 24 * 60 * (60 / self.tess["info_tess"]["period"])
                tokens["[token_tess_period_seconds]"] = self.tess["info_tess"]["period"]

        if "info_location" in self.tess:
            if "place" in self.tess["info_location"] and "country" in self.tess["info_location"]:
                tokens["[token_tess_sunmoon_datasource]"] = self.tess["name"] + \
                    " (" + self.tess["info_location"]["country"] + ") " + self.tess["info_location"]["place"]
                tokens["[token_tess_sunmoon_datasource_escape]"] = re.escape(tokens["[token_tess_sunmoon_datasource]"])

        return tokens

    def __generate_tess_images_tokens(self):
        tokens = {
            "[token_tess_images_arr]": []
        }

        if "info_img" in self.tess and "urls" in self.tess["info_img"]:
            tokens["[token_tess_images_arr]"] = [str(x) for x in self.tess["info_img"]["urls"]]

        return tokens

    def __set_defaults(self):
        default_info = {
            "name": "TESS Photometer",
            "logo_url": "http://tess.stars4all.eu/wp-content/uploads/2018/01/TESS_logo_web.png",
            "description": "The Telescope Encoder and Sky Sensor (TESS-W) is the first model of TESS photometers, compact devices to monitor sky brightness every night.<br><br>Designed by astronomers and calibrated on LICA laboratory at Universidad Complutense de Madrid the quality of the data is scientifically accurate.<br><br>TESS photometer is mounted on a weatherproof enclosure. Wherever there is electricity and WIFI you can install it and get the measures online trough the remote observatory.<br><br>Its temperature and IR sensor will let you know whether the sky is clear or cloudy.<br><br>Browse the poster presented during the IAU 2018 in Vienna<br><br>Or check the article describing the device by Jaime Zamorano et al. 2016 The International Journal of Sustainable Lighting 35 (2016) 49-54 <a href='http://www.lightingjournal.org/index.php/path/article/view/21/24'>http://doi.org/10.22644/ijsl.2016.35.1.049:</a>",
            "web_url": "http://tess.stars4all.eu/",
            "phone": "(+34) 924 00 34 13",
            "mail": "jzamorano@fis.ucm.es"
        }

        if "info_org" not in self.tess or not self.tess["info_org"]:
            self.tess["info_org"] = default_info

        if "logo_url" not in self.tess["info_org"] and "web_url" not in self.tess["info_org"]:
            self.tess["info_org"]["logo_url"] = default_info["logo_url"]
            self.tess["info_org"]["web_url"] = default_info["web_url"]

        if "info_location" in self.tess:
            if self.tess["info_location"].get("latitude", None) and self.tess["info_location"].get("longitude", None):
                my_location = Location(self.tess["info_location"], self.tess["name"], self.tess["mac"], self.api_url)
                self.tess["info_location"] = my_location.getLocation()

    def generate_tokens(self, grafana_url, grafana_org_id):
        tokens = {
            "[token_tess_id]": self.tess["name"],
            "[token_grafana_url]": grafana_url,
            "[token_grafana_org_id]": grafana_org_id,
            "[token_grafana_dash_raw]": grafana_url + "/d/tess_raw/s4a-photometer-network-raw?orgId=" + str(grafana_org_id) + "&var-Tess=" + self.tess["name"],
            "[token_grafana_dash_datasheet]": grafana_url + "/d/datasheet_" + self.tess["name"] + "/" + self.tess["name"] + "?orgId=" + str(grafana_org_id)
        }

        self.__set_defaults()

        tokens.update(self.__generate_css_tokens())
        tokens.update(self.__generate_tess_location_tokens())
        tokens.update(self.__generate_tess_org_tokens())
        tokens.update(self.__generate_tess_contact_tokens())
        tokens.update(self.__generate_tess_tokens())
        tokens.update(self.__generate_tess_images_tokens())
        return tokens
