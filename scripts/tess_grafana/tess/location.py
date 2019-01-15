import requests
import copy
# from geopy.geocoders import Nominatim, ArcGIS, Photon


class Location:
    def __init__(self, location={}, name=None, mac=None, api_url=None):
        self.location = location

        try:
            old_location = copy.deepcopy(self.location)
            if not self.__isComplete():
                self.__nominatim()

            if not self.__isComplete():
                self.__photon()

            if old_location != self.location and name and mac and api_url:
                r = requests.post("%s/photometers/%s/%s" % (api_url, name, mac),
                                  json={'tess': {'info_location': self.location}, 'noexec': True})
        except:
            pass

    def __isComplete(self):
        return self.location.get("country", None) and self.location.get("region", None) and self.location.get("sub_region", None) and self.location.get("town", None)

    def __photon(self):
        try:
            from geopy.geocoders import Photon
            geolocator = Photon(timeout=15)
            location = geolocator.reverse(str(self.location["latitude"]) + "," +
                                          str(self.location["longitude"]), exactly_one=True)

            if not self.location.get("country", None) and "country" in location.raw["properties"]:
                self.location["country"] = location.raw["properties"]["country"]
            if not self.location.get("region", None) and "state" in location.raw["properties"]:
                self.location["region"] = location.raw["properties"]["state"]

            if not self.location.get("town", None) and "city" in location.raw["properties"]:
                self.location["town"] = location.raw["properties"]["city"]
        except:
            pass

    def __nominatim(self):
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="my-application", timeout=15)
            location = geolocator.reverse(str(self.location["latitude"]) + "," +
                                          str(self.location["longitude"]), exactly_one=True, language="en")

            if not self.location.get("country", None) and "country" in location.raw["address"]:
                self.location["country"] = location.raw["address"]["country"]

            if not self.location.get("region", None) and "state" in location.raw["address"]:
                self.location["region"] = location.raw["address"]["state"]

            if not self.location.get("sub_region", None) and "county" in location.raw["address"]:
                self.location["sub_region"] = location.raw["address"]["county"]

            if not self.location.get("town", None) and "town" in location.raw["address"]:
                self.location["town"] = location.raw["address"]["town"]

        except:
            pass

    # def __fill(self):
    #     if not self.location.get("country", None) or not self.location.get("region", None) or not self.location.get("sub_region", None):
    #         try:
    #             from geopy.geocoders import Photon
    #             geolocator_Photon = Photon(timeout=15)
    #
    #             location = geolocator_Photon.reverse(str(self.location["latitude"]) + "," + str(self.location["longitude"]), exactly_one=True)
    #
    #             if not self.location.get("country", None) and "country" in location.raw["properties"]:
    #                 self.location["country"] = location.raw["properties"]["country"]
    #
    #             if not self.location.get("region", None) and "state" in location.raw["properties"]:
    #                 self.location["region"] = location.raw["properties"]["state"]
    #
    #             if not self.location.get("sub_region", None) and "city" in location.raw["properties"]:
    #                 self.location["sub_region"] = location.raw["properties"]["city"]
    #
    #             #TODO store in server side
    #         except:
    #             pass

    def getLocation(self):
        # self.__fill()
        return self.location
