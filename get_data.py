import requests
from requests.auth import HTTPBasicAuth
import time
import datetime
import json
import pdb
import re

class CustomsHouse:

    def __init__(self):
        self.key = "fyL_t9f4wAZX4CTggjXs-TFkd1XaWi9H_RbSeRai"
        self.base_url = "https://api.companieshouse.gov.uk/"


    def get_company_details(self, name, items_per_page=1000):
        payload = {'q': name, "items_per_page": items_per_page}
        return requests.get(self.base_url + "search/companies", params=payload, auth=HTTPBasicAuth(self.key, ""))

    def get_company_number(self, company):
        return company["company_number"]

    def get_name_guid(self, directors, count):
        directorships = []
        for d in directors:
            try:
                if "officer_role" in d:
                    if d["officer_role"] == "director":
                        directorships.append(d["name"] + " :  " + self.get_guid(str(d["links"]["officer"]["appointments"])))
            except json.decoder.JSONDecodeError:
                if directors.status_code == 429:
                    print("429 received", datetime.datetime.now())
                    return count, directorships
            except KeyError:
                print(d)
                pdb.set_trace()

        return count, directorships



    def get_guid(self, link):
        try:
            director_guid = re.search("/officers/(.+)/appointments", link).group(1)
        except AttributeError:
            print("no director guid found")
            raise AttributeError
        return director_guid

    def get_companies_of_director(self, director, count):
        directorships = []
        director_guid = self.get_guid(director)
        try:
            appointments = requests.get(self.base_url[:-1] + director, auth=HTTPBasicAuth(self.key, ""))
            appointments = appointments.json()["items"]
        except json.decoder.JSONDecodeError:
            if appointments.status_code == 429:
                print("429 received", datetime.datetime.now())
                print("count at", count)
                time.sleep(5 * 60)
                return 1, director_guid, None
            else:
                print(director)
                print(appointments)
                return count +1, director_guid, None
        except KeyError:
            return count+1, director_guid, None

        for i in appointments:
            if "director" in str(i["officer_role"]):
                directorships.append(i["appointed_to"]["company_number"])
        if len(directorships) < 1:
            return count+1, director_guid, None
        else:
            return count+1, director_guid, directorships

    def get_dirs(self, company_number, count):
        return count + 1, requests.get(self.base_url +"company/" + str(company_number) + "/officers", auth=HTTPBasicAuth(self.key, ""))


