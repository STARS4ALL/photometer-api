# coding=utf-8
from grafana.grafana_api import GrafanaAPI

from deepdiff import DeepDiff
import re
from copy import deepcopy
import json
import random
import copy

class TessGrafana(object):
    def __init__(self, user, paswd, org_template, org_production, protocol, host):
        self.grafana_template_org_id = org_template
        self.grafana_final_org_id = org_production
        self.grafana_host = host
        self.grafana_protocol = protocol
        self.grafana_api = GrafanaAPI((user, paswd),  host=host, url_path_prefix='', protocol=protocol)

        self.grafana_api.switch_actual_user_organisation(self.grafana_template_org_id)
        self.grafana_template_preferences = self.grafana_api.get_user_preferences()

        self.grafana_api.switch_actual_user_organisation(self.grafana_final_org_id)
        self.grafana_api.update_user_preferences(
            {"timezone": self.grafana_template_preferences["timezone"], "theme": self.grafana_template_preferences["theme"]})

    def __replafe_all_tokens(self, tess_object, template_string):
        for key in tess_object.keys():

            # try:
            if isinstance(tess_object[key], basestring):
                if isinstance(tess_object[key], unicode):
                    # print(tess_object[key])
                    template_string = template_string.replace(key, tess_object[key])
                else:
                    template_string = template_string.replace(key, unicode(str(tess_object[key]).encode('utf8'), "utf-8"))

            else:
                template_string = template_string.replace(key, str(tess_object[key]))
            # except ValueError as e:
            #     print(e)
            #     print(key,tess_object[key])
            #     exit()

        return template_string

    def __get_next_id(self, A):
        return next(i for i, e in enumerate(sorted(A) + [None], 0) if i != e)

    def __fix_gridPos(self, panels, allowGridPanel=False, ps=False):
        # Panel that support gird mode are define with isGridPanel:true
        _y = 0
        _x = 0
        for panel in panels:
            if allowGridPanel or ("isGridPanel" in panel and panel["isGridPanel"] == True):
                panel["gridPos"]["y"] = _y
                panel["gridPos"]["x"] = _x
                _x += panel["gridPos"]["w"]
                if _x == 24:
                    _y += panel["gridPos"]["h"]
                    _x = 0
            else:
                panel["gridPos"]["y"] = _y
                _y += panel["gridPos"]["h"]

            if ps:
                print(panel["gridPos"], panel["id"], panel["title"])
        return panels

    def __find_template(self, template_uid):
        self.grafana_api.switch_actual_user_organisation(self.grafana_template_org_id)  # Force to use Template Org.
        template_dash = self.grafana_api.get_dashboard_by_uid(template_uid)
        if "dashboard" in template_dash and template_dash["dashboard"]["id"] == self.grafana_template_preferences["homeDashboardId"]:
            template_dash["meta"]["isHomeDash"] = True
        return template_dash

    def __find_dash_by_uid(self, uid):
        self.grafana_api.switch_actual_user_organisation(self.grafana_final_org_id)  # Force to use Main Org.
        return self.grafana_api.get_dashboard_by_uid(uid)

    def __replace_template_tokens(self, template_dash, tess_object):
        # Replace All Tokens
        # dash_info_template_string = json.dumps(dash_info_template)
        # for key in tess_object.keys():
        #     dash_info_template_string = dash_info_template_string.replace(key, tess_object[key])
        dash_info_template_string = self.__replafe_all_tokens(tess_object, json.dumps(template_dash))

        # Comprobar si fueron reemplazados todos los tokens
        p = re.compile('\[token_\w+\]', re.IGNORECASE)
        if p.findall(dash_info_template_string):
            return ({"status": "error", "error": "No replace all tokens: ", "tokens": p.findall(dash_info_template_string)})

        return json.loads(dash_info_template_string)

    def __find_dash_by_title(self, title):
        self.grafana_api.switch_actual_user_organisation(self.grafana_final_org_id)  # Force to use Main Org.
        results = self.grafana_api.search_dashboard_or_folder(query=title)

        # Remove all dash that not are the same exactly the same title
        for result in results:
            if result["title"] != title:
                results.remove(result)

        return results

    def __find_folder_id(self, title):
        results = self.__find_dash_by_title(title)
        for result in results:
            if result["type"] != "dash-folder":
                results.remove(result)

        if results:
            return results[0]["id"]

        return None

    def __create_folder(self, title, uid=None):
        # Search folder with this tittle
        folder_id = self.__find_folder_id(title)

        if not folder_id:
            result = self.grafana_api.create_folder(title=title, uid=uid)
            if "id" in result:
                folder_id = result["id"]

        return folder_id

    def __create_dash_from_template(self, dash_template, uid=None, message="Create Dash"):
        # Crear dashboard con el título y los paneles para el tess...
        dash_template["dashboard"]["id"] = None
        dash_template["dashboard"]["uid"] = uid
        dash_template["message"] = message

        self.grafana_api.switch_actual_user_organisation(self.grafana_final_org_id)  # Force to use Main Org.
        return self.grafana_api.create_or_update_dashboard(dash_template)

    def __update_dash(self, dash, message="Update Dash"):
        # Add message
        dash["message"] = message

        # save
        self.grafana_api.switch_actual_user_organisation(self.grafana_final_org_id)  # Force to use Main Org.
        return self.grafana_api.create_or_update_dashboard(dash)

    def __set_starred_configuration(self, response, dash_info_template):
        if "id" in response:
            if "meta" in dash_info_template and "isStarred" in dash_info_template["meta"] and dash_info_template["meta"]["isStarred"]:
                self.grafana_api.star_actual_user_dashboard(response["id"])
            else:
                self.grafana_api.unstar_actual_user_dashboard(response["id"])

            if "meta" in dash_info_template and "isHomeDash" in dash_info_template["meta"] and dash_info_template["meta"]["isHomeDash"]:
                self.grafana_api.update_user_preferences({"homeDashboardId": response["id"]})

    def add_or_update_tess_in_country_list(self, tess_object):
        DASH_TEMPLATE_UID = "template_tess_by_regions"  # uid dash template
        DASH_FINAL_UID = "tess_country_" + tess_object["[token_tess_location_country]"].replace(" ", "_")

        # Load template
        dash_info_template = self.__find_template(DASH_TEMPLATE_UID)

        if not "dashboard" in dash_info_template:
            return ({"status": "error", "error": "No exist template " + DASH_TEMPLATE_UID + " in organisation " + str(self.grafana_template_org_id)})

        # Updete Folder ID
        dash_info_template["folderId"] = self.__create_folder(dash_info_template["meta"]["folderTitle"])

        # Replace All Tokens
        dash_info_template = self.__replace_template_tokens(dash_info_template, tess_object)
        if "status" in dash_info_template and dash_info_template["status"] == "error":
            return dash_info_template

        # Search dashboards with this tittle
        results = self.__find_dash_by_title(dash_info_template["dashboard"]["title"])

        # Generate Sun And Moon datasources
        self.generate_sunmoon_datasource(tess_object)

        response = None

        if results:
            message = "Update Dash and"
            # Si ya existe el dashboard
            dash_info = self.__find_dash_by_uid(results[0]['uid'])

            # Remove statics panels
            p = re.compile('stars\d+', re.IGNORECASE)
            in_use_ids = []
            for panel_info in dash_info["dashboard"]["panels"][:]:
                in_use_ids.append(panel_info["id"])

            # Comprobar si existen los paneles en el dash
            panels_ids = []
            # Obtener los paneles del dash que ya contengan el tess_id
            p = re.compile('stars\d+', re.IGNORECASE)
            for idx, panel_info in enumerate(dash_info["dashboard"]["panels"]):
                panel_info_string = json.dumps(panel_info).replace('stars4all', '')
                if tess_object["[token_tess_id]"] in p.findall(panel_info_string):
                    panels_ids.append(idx)

            # Comprobar el estado de los paneles
            if len(panels_ids) == 0:
                message += " added Tess: " + tess_object["[token_tess_id]"]
                # Añadir los paneles nuevos
                for idx in range(len(dash_info_template["dashboard"]["panels"])):
                    dash_info_template["dashboard"]["panels"][idx]["id"] = self.__get_next_id(in_use_ids)
                    in_use_ids.append(self.__get_next_id(in_use_ids))
                    dash_info["dashboard"]["panels"].append(dash_info_template["dashboard"]["panels"][idx])

            else:
                message += " update Tess: " + tess_object["[token_tess_id]"]
                # Actualizar los paneles que ya existen y añadir los que faltan
                template_id_change = []
                for idx in range(len(panels_ids)):
                    for idx_template, panel_template in enumerate(dash_info_template["dashboard"]["panels"]):
                        diff = DeepDiff(dash_info["dashboard"]["panels"][panels_ids[idx]], panel_template)
                        if any(elem in ["dictionary_item_added", "dictionary_item_removed", "iterable_item_removed", "type_changes", "iterable_item_added"] for elem in diff.keys()):
                            continue
                        panel_template["id"] = dash_info["dashboard"]["panels"][panels_ids[idx]]["id"]
                        template_id_change.append(idx_template)

                for idx_template, panel_template in enumerate(dash_info_template["dashboard"]["panels"]):
                    if idx_template not in template_id_change:
                        panel_template["id"] = self.__get_next_id(in_use_ids)
                        in_use_ids.append(self.__get_next_id(in_use_ids))

                # Eliminar los paneles viejos
                panels_ids.sort(reverse=True)
                for idx in panels_ids:
                    dash_info["dashboard"]["panels"].pop(idx)
                panels_ids.sort(reverse=False)

                # Añadir los paneles nuevos guardando la posicion anterior
                len_template = len(dash_info_template["dashboard"]["panels"])
                div_result = divmod(panels_ids[0], len_template)
                if div_result[1] == 0:
                    start_pos = div_result[0] * (len_template)
                else:
                    start_pos = (div_result[0] + 1) * (len_template)

                for idx in range(len_template):
                    dash_info["dashboard"]["panels"].insert(start_pos + idx, dash_info_template["dashboard"]["panels"][idx])

            # Sort
            try:
                arr_no_sort = []
                for i in range(0, len(dash_info["dashboard"]["panels"]), len(dash_info_template["dashboard"]["panels"])):
                    stars_ids = re.findall('\d+', dash_info["dashboard"]["panels"][i]["title"])
                    arr_no_sort.append({"idx": i, "starsid": int(stars_ids[0])})

                arr_sort = sorted(arr_no_sort, key=lambda k: k['starsid'])

                if arr_no_sort != arr_sort:
                    temp_panesl = []

                    for item in arr_sort:
                        for idx in range(len(dash_info_template["dashboard"]["panels"])):
                            temp_panesl.append(dash_info["dashboard"]["panels"][item["idx"] + idx])

                    dash_info["dashboard"]["panels"] = temp_panesl

            except:
                pass

            # Copy annotations and variables
            dash_info["dashboard"]["templating"] = dash_info_template["dashboard"]["templating"]
            dash_info["dashboard"]["annotations"] = dash_info_template["dashboard"]["annotations"]

            # Fix gridPos
            dash_info["dashboard"]["panels"] = self.__fix_gridPos(dash_info["dashboard"]["panels"])

            # Set uid
            dash_info["dashboard"]["uid"] = DASH_FINAL_UID

            # Save
            response = self.__update_dash(dash_info, message=message + " " + str(panels_ids))

        else:
            # Create
            response = self.__create_dash_from_template(
                dash_info_template, message="Create Dash and added Tess: " + tess_object["[token_tess_id]"], uid=DASH_FINAL_UID)

        self.__set_starred_configuration(response, dash_info_template)
        return(response)

    def add_or_update_tess_in_lastet_measures(self, tess_object):
        DASH_TEMPLATE_UID = "template_tess_latest_measures"  # uid dash template
        DASH_FINAL_UID = "tess_latest_measures"
        STATIC_PANELS = 0  # Total de paneles estaticos que hay al comienzo del dashboard

        # Load template
        dash_info_template = self.__find_template(DASH_TEMPLATE_UID)

        if not "dashboard" in dash_info_template:
            return ({"status": "error", "error": "No exist template " + DASH_TEMPLATE_UID + " in organisation " + str(self.grafana_template_org_id)})

        # Updete Folder ID
        dash_info_template["folderId"] = self.__create_folder(dash_info_template["meta"]["folderTitle"])

        # Replace All Tokens
        dash_info_template = self.__replace_template_tokens(dash_info_template, tess_object)
        if "status" in dash_info_template and dash_info_template["status"] == "error":
            return dash_info_template

        # Search dashboards with this tittle
        results = self.__find_dash_by_title(dash_info_template["dashboard"]["title"])

        response = None

        if results:
            # print("Si Existe el dashboard para este país")
            dash_info = self.grafana_api.get_dashboard_by_uid(results[0]['uid'])

            # Remove statics panels
            p = re.compile('stars\d+', re.IGNORECASE)
            in_use_ids = []
            for panel_info in dash_info["dashboard"]["panels"][:]:
                panel_info_string = json.dumps(panel_info)
                if not p.findall(panel_info_string):
                    dash_info["dashboard"]["panels"].remove(panel_info)
                else:
                    in_use_ids.append(panel_info["id"])

            # Set unused id to static panels
            for idx in range(STATIC_PANELS):
                dash_info_template["dashboard"]["panels"][idx]["id"] = self.__get_next_id(in_use_ids)
                in_use_ids.append(self.__get_next_id(in_use_ids))

            # Append static panels
            dash_info["dashboard"]["panels"] = dash_info_template["dashboard"]["panels"][:STATIC_PANELS] + dash_info["dashboard"]["panels"]

            # Fix gridPos
            dash_info["dashboard"]["panels"] = self.__fix_gridPos(dash_info["dashboard"]["panels"], allowGridPanel=True)

            # Comprobar si existen los paneles en el dash
            panels_ids = []
            # Obtener los paneles del dash que ya contengan el tess_id
            p = re.compile('stars\d+', re.IGNORECASE)
            for idx, panel_info in enumerate(dash_info["dashboard"]["panels"]):
                panel_info_string = json.dumps(panel_info).replace('stars4all', '')
                if tess_object["[token_tess_id]"] in p.findall(panel_info_string):
                    panels_ids.append(idx)

            # Comprobar el estado de los paneles
            if len(panels_ids) == 0:
                # Añadir los paneles nuevos
                for idx in range(len(dash_info_template["dashboard"]["panels"][STATIC_PANELS:])):
                    dash_info_template["dashboard"]["panels"][idx + STATIC_PANELS]["id"] = self.__get_next_id(in_use_ids)
                    in_use_ids.append(self.__get_next_id(in_use_ids))
                    dash_info["dashboard"]["panels"].append(dash_info_template["dashboard"]["panels"][idx + STATIC_PANELS])

            else:
                # Obtener el id de los paneles que ya existen
                for idx in range(len(panels_ids)):
                    for idx_template, panel_template in enumerate(dash_info_template["dashboard"]["panels"]):
                        diff = DeepDiff(dash_info["dashboard"]["panels"][panels_ids[idx]], panel_template)
                        if any(elem in ["dictionary_item_added", "dictionary_item_removed", "iterable_item_removed", "type_changes", "iterable_item_added"] for elem in diff.keys()):
                            continue
                        panel_template["id"] = dash_info["dashboard"]["panels"][panels_ids[idx]]["id"]
                        panel_template["gridPos"] = dash_info["dashboard"]["panels"][panels_ids[idx]]["gridPos"]
                        dash_info["dashboard"]["panels"][panels_ids[idx]] = panel_template

            # Sort
            try:
                arr_no_sort = []
                for i in range(STATIC_PANELS, len(dash_info["dashboard"]["panels"]), len(dash_info_template["dashboard"]["panels"]) - STATIC_PANELS):
                    stars_ids = re.findall('\d+', dash_info["dashboard"]["panels"][i]["title"])
                    arr_no_sort.append({"idx": i, "starsid": int(stars_ids[0])})

                arr_sort = sorted(arr_no_sort, key=lambda k: k['starsid'])

                if arr_no_sort != arr_sort:
                    temp_panesl = []
                    for panel in dash_info_template["dashboard"]["panels"][:STATIC_PANELS]:
                        temp_panesl.append(panel)

                    for item in arr_sort:
                        for idx in range(len(dash_info_template["dashboard"]["panels"]) - STATIC_PANELS):
                            temp_panesl.append(dash_info["dashboard"]["panels"][item["idx"] + idx])

                    dash_info["dashboard"]["panels"] = temp_panesl

            except:
                pass

            # Fix gridPos
            dash_info["dashboard"]["panels"] = self.__fix_gridPos(dash_info["dashboard"]["panels"], allowGridPanel=True)

            # Set uid
            dash_info["dashboard"]["uid"] = DASH_FINAL_UID

            # Save
            response = self.__update_dash(dash_info, message="Update Tess: " + tess_object["[token_tess_id]"])

        else:
            # Create
            response = self.__create_dash_from_template(
                dash_info_template, message="Create Dash and added Tess: " + tess_object["[token_tess_id]"], uid=DASH_FINAL_UID)

        self.__set_starred_configuration(response, dash_info_template)
        return(response)

    def __add_to_filter_list(self, tess_object, template_uid, dash_final_uid, default_options):

        # Load template
        dash_info_template = self.__find_template(template_uid)

        if not "dashboard" in dash_info_template:
            return ({"status": "error", "error": "No exist template " + template_uid + " in organisation " + str(self.grafana_template_org_id)})

        # Updete Folder ID
        dash_info_template["folderId"] = self.__create_folder(dash_info_template["meta"]["folderTitle"])

        # Search dashboards with this tittle
        results = self.__find_dash_by_title(dash_info_template["dashboard"]["title"])

        if not results:

            response = self.__create_dash_from_template(dash_info_template, uid=dash_final_uid)
            uid = response["uid"]
        else:
            uid = results[0]['uid']

        dash_info = self.grafana_api.get_dashboard_by_uid(uid)

        # get dash_info first templating list options and query and add new tess and then add options and query to template dash
        old_query = dash_info["dashboard"]["templating"]["list"][0]["query"]
        old_options = dash_info["dashboard"]["templating"]["list"][0]["options"]

        if tess_object["[token_tess_id]"] not in old_query.split(","):
            if old_query:
                old_query += "," + str(tess_object["[token_tess_id]"])
                old_options.append(default_options)
            else:
                old_query = str(tess_object["[token_tess_id]"])
                old_options = [default_options]
        else:
            for position, item in enumerate(old_options):
                if item['value'] == tess_object["[token_tess_id]"]:
                    old_options[position] = default_options

        # Keep new panel style
        dash_info_template["dashboard"]["id"] = dash_info["dashboard"]["id"]
        dash_info_template["dashboard"]["uid"] = dash_info["dashboard"]["uid"]
        dash_info["dashboard"] = dash_info_template["dashboard"]

        # set all options with selected False
        # sort options
        for opt in old_options:
            opt["selected"] = False
            opt["tess_id_number"] = int(re.findall('\d+', opt["value"])[0])

        options_sort = sorted(old_options, key=lambda k: k['tess_id_number'])


        for list_template in dash_info["dashboard"]["templating"]["list"]:
            list_template["query"] = old_query
            list_template["options"] = copy.deepcopy(options_sort)

        # Random option selected
        for list_template in dash_info["dashboard"]["templating"]["list"]:
            selected_pos = random.randint(0, len(list_template["options"]) - 1)
            list_template["current"] = list_template["options"][selected_pos]
            list_template["options"][selected_pos]["selected"] = True

        dash_info["overwrite"] = True

        # Set uid
        dash_info["dashboard"]["uid"] = dash_final_uid

        # Save
        # response = self.grafana_api.create_or_update_dashboard(dash_info)
        response = self.__update_dash(dash_info)
        self.__set_starred_configuration(response, dash_info_template)
        return(response)

    def __search_alert_notification(self, alert_name):
        all_alerts = self.grafana_api.get_alert_notifications()
        for alert in all_alerts:
            if alert["name"] == alert_name:
                return alert
        return None

    def __parse_emails(self, addressToVerify):
        if addressToVerify:
            import re

            emails = []

            for email in addressToVerify.split(";"):
                match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)

                if match == None:
                    print('Bad Syntax')
                    raise ValueError('Bad Syntax')
                else:
                    emails.append(email)

            return ';'.join(emails)

        else:
            return addressToVerify

    def generate_sunmoon_datasource(self, tess_object):
        if tess_object["[token_tess_sunmoon_datasource]"]:
            self.grafana_api.switch_actual_user_organisation(self.grafana_final_org_id)
            datasource_sunmoon = self.grafana_api.get_datasource_by_name(tess_object["[token_tess_sunmoon_datasource]"])

            datasource_sunmoon_object = {
                "orgId": 1,
                "name": tess_object["[token_tess_sunmoon_datasource]"],
                "type": "fetzerch-sunandmoon-datasource",
                "access": "proxy",
                "basicAuth": False,
                "withCredentials": False,
                "isDefault": False,
                "jsonData": {
                    "keepCookies": [],
                    "position": {
                        "latitude": tess_object["[token_tess_location_lat]"],
                        "longitude": tess_object["[token_tess_location_lon]"]
                    }
                },
                "readOnly": False}

            if datasource_sunmoon and "id" in datasource_sunmoon:
                # update
                datasource_sunmoon_object["id"] = datasource_sunmoon["id"]
                self.grafana_api.switch_actual_user_organisation(self.grafana_final_org_id)
                datasource_sunmoon = self.grafana_api.update_datasource(datasource_sunmoon["id"], datasource_sunmoon_object)
            else:
                # create
                self.grafana_api.switch_actual_user_organisation(self.grafana_final_org_id)
                datasource_sunmoon = self.grafana_api.create_datasource(datasource_sunmoon_object)

    def add_or_update_tess_in_comparison(self, tess_object):
        DASH_TEMPLATE_UID = "template_tess_comparison"  # uid dash template
        DASH_FINAL_UID = "tess_comparison"
        # Add to templating.list[all].options and query
        default_options = {
            "selected": False,
            "text": tess_object["[token_tess_id]"] + " - " + tess_object["[token_tess_location_place_country]"],
            "value": tess_object["[token_tess_id]"]
        }
        return self.__add_to_filter_list(tess_object, DASH_TEMPLATE_UID, DASH_FINAL_UID, default_options)

    def add_or_update_tess_in_heatmap(self, tess_object):
        DASH_TEMPLATE_UID = "template_tess_heatmap"  # uid dash template
        DASH_FINAL_UID = "tess_heatmap"
        # Add to templating.list[all].options and query
        default_options = {
            "selected": False,
            "text": tess_object["[token_tess_id]"] + " - " + tess_object["[token_tess_location_place_country]"],
            "value": tess_object["[token_tess_id]"]
        }
        return self.__add_to_filter_list(tess_object, DASH_TEMPLATE_UID, DASH_FINAL_UID, default_options)

    def add_or_update_tess_in_statistics(self, tess_object):
        DASH_TEMPLATE_UID = "template_tess_statistics"  # uid dash template
        DASH_FINAL_UID = "tess_statistics"
        # Add to templating.list[all].options and query
        default_options = {
            "selected": False,
            "text": tess_object["[token_tess_id]"] + " - " + tess_object["[token_tess_location_place_country]"],
            "value": tess_object["[token_tess_id]"]
        }
        return self.__add_to_filter_list(tess_object, DASH_TEMPLATE_UID, DASH_FINAL_UID, default_options)

    def add_or_update_tess_in_raw(self, tess_object):
        DASH_TEMPLATE_UID = "template_tess_raw"  # uid dash template
        DASH_FINAL_UID = "tess_raw"

        # Add to templating.list[all].options and query
        default_options = {
            "selected": False,
            "text": tess_object["[token_tess_id]"] + " - " + tess_object["[token_tess_location_place_country]"],
            "value": tess_object["[token_tess_id]"]
        }
        return self.__add_to_filter_list(tess_object, DASH_TEMPLATE_UID, DASH_FINAL_UID, default_options)

    def generate_datasheet(self, tess_object):
        DASH_TEMPLATE_UID = "datasheet_token_tess_id"
        DASH_FINAL_UID = "datasheet_" + tess_object["[token_tess_id]"]
        # datasheet uid need be override with datasheet_tessId -> datasheet_stars1
        # check that alert email is set!!
        # check that folder is the same!
        # Load template

        dash_info_template = self.__find_template(DASH_TEMPLATE_UID)

        if not "dashboard" in dash_info_template:
            return ({"status": "error", "error": "No exist template " + DASH_TEMPLATE_UID + " in organisation " + str(self.grafana_template_org_id)})

        # self.grafana_api.switch_actual_user_organisation(self.grafana_final_org_id)
        # print(self.grafana_api.create_folder("Datasheet",'datasheet'))

        # Updete Folder ID
        dash_info_template["folderId"] = self.__create_folder(
            dash_info_template["meta"]["folderTitle"], "datasheet_" + str(self.grafana_final_org_id))

        # Replace All Tokens
        dash_info_template = self.__replace_template_tokens(dash_info_template, tess_object)
        if "status" in dash_info_template and dash_info_template["status"] == "error":
            return dash_info_template

        # Generate Sun And Moon datasources
        self.generate_sunmoon_datasource(tess_object)

        alert_notification = self.__search_alert_notification(tess_object["[token_tess_id]"])
        # Configure Email notification alert!
        if tess_object["[token_tess_contact_mail]"]:
            alert_object = {
                "name": tess_object["[token_tess_id]"],
                "type": "email",
                "isDefault": False,
                "sendReminder": False,
                "settings": {
                    "addresses": self.__parse_emails(tess_object["[token_tess_contact_mail]"])
                }
            }
            # Create or update alerts
            if alert_notification:
                # update
                alert_object["id"] = alert_notification["id"]
                alert_notification = self.grafana_api.update_alert_notifications(alert_notification["id"], alert_object)
            else:
                # create
                alert_notification = self.grafana_api.create_alert_notifications(alert_object)
        else:
            # Delete alert!
            if alert_notification:
                self.grafana_api.delete_alert_notifications(alert_notification["id"])
                alert_notification = None

        # TODO remove only notifications generated by this script
        notifications = []
        if alert_notification and "id" in alert_notification:
            notifications.append({"id": alert_notification["id"]})

        # Add alert notification to alert panel
        for panel in dash_info_template["dashboard"]["panels"]:
            if "alert" in panel:
                panel["alert"]["notifications"] = notifications

        dash_info = self.grafana_api.get_dashboard_by_uid(DASH_FINAL_UID)
        if("dashboard" in dash_info):
            dash_info_template["dashboard"]["id"] = dash_info["dashboard"]["id"]
            dash_info_template["dashboard"]["uid"] = DASH_FINAL_UID

            dash_info_template["overwrite"] = True

            response = self.__update_dash(dash_info_template)
        else:
            response = self.__create_dash_from_template(dash_info_template, uid=DASH_FINAL_UID)

        self.__set_starred_configuration(response, dash_info_template)
        return(response)

    def generate_map(self, tess_object):
        DASH_TEMPLATE_UID = "template_tess_network_map"
        DASH_FINAL_UID = "tess_network_map"

        # http://upm.tess-dashboards.stars4all.eu/api/user/stars/dashboard/123   set as favorite

        # Load template
        dash_info_template = self.__find_template(DASH_TEMPLATE_UID)

        if not "dashboard" in dash_info_template:
            return ({"status": "error", "error": "No exist template " + DASH_TEMPLATE_UID + " in organisation " + str(self.grafana_template_org_id)})

        # Updete Folder ID
        dash_info_template["folderId"] = self.__create_folder(
            dash_info_template["meta"]["folderTitle"], "datasheet_" + str(self.grafana_final_org_id))

        # Replace All Tokens
        dash_info_template = self.__replace_template_tokens(dash_info_template, tess_object)
        if "status" in dash_info_template and dash_info_template["status"] == "error":
            return dash_info_template

        dash_info = self.grafana_api.get_dashboard_by_uid(DASH_FINAL_UID)
        if("dashboard" in dash_info):
            dash_info_template["dashboard"]["id"] = dash_info["dashboard"]["id"]
            dash_info_template["dashboard"]["uid"] = DASH_FINAL_UID

            dash_info_template["overwrite"] = True

            response = self.__update_dash(dash_info_template)
        else:
            response = self.__create_dash_from_template(dash_info_template, uid=DASH_FINAL_UID)

        self.__set_starred_configuration(response, dash_info_template)
        return(response)
