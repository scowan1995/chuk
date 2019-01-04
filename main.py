from get_data import CustomsHouse
import time
import datetime
import random
import networkx as nx
import json
import itertools
import pickle

class Main:

    def __init__(self, companies):
        self.timeout = 60 * 5
        self.companies_dirs = {}  # company number : [directors]
        self.company_statuses = []
        self.unused_companies = []
        self.companies_list = companies
        self.used = set()
        self.ch = CustomsHouse()

    def add_dirs(self, companies):
        for c in companies:
            c_num = self.ch.get_company_number(c)
            if c_num not in self.companies_dirs:
                self.companies_dirs[c_num] = self.ch.get_dirs(c)

    def get_starter_companies(self):
        for company in self.companies_list:
            details = self.ch.get_company_details(company).json()#["items"]
            for c in details["items"]:
                company_number = c["company_number"]
                if c["company_status"] not in self.company_statuses:
                    self.company_statuses.append(c["company_status"])
                if c["company_status"] == "open" or c["company_status"] == "active":
                    self.unused_companies.append(company_number)
        random.shuffle(self.unused_companies)


    def get_list_of_companies(self):
        self.get_starter_companies()
        time.sleep(self.timeout)
        # select a random company, for now pop first
        iters = 30
        for j in range(iters):
            print("on iter:", j)
            print("time of iter", datetime.datetime.now())
            t_5mins = time.time() + self.timeout
            i = 1
            while i < 600:
                if i % 100 == 0:
                    print("requests at", i)
                if len(self.unused_companies) < 1:
                    print("No companies left")
                random_company = -1
                got_unique = False
                while not got_unique:
                    random_company = self.unused_companies.pop(random.randrange(0, len(self.unused_companies)))
                    if random_company not in self.used:
                        got_unique = True
                self.used.add(random_company)
                # get the companies directors
                i, directors = self.ch.get_dirs(random_company, i)
                if directors.status_code == 429:
                    print("got a 429 in main")
                    time.sleep(self.timeout)
                else:
                    try:
                        directors = directors.json()["items"]
                    except KeyError:
                        continue
                self.companies_dirs[random_company] = directors
                # get the companies associated with those directors and add to the unused companies list
                for d in directors:
                    i, director_guid, new_companies = self.ch.get_companies_of_director(d["links"]["officer"]["appointments"], i)
                    if new_companies is not None:
                        self.unused_companies += new_companies
            wait = 3 + (t_5mins - time.time())
            if wait > 0:
                time.sleep(wait)
            self.final_companies = self.used.union(self.unused_companies)
            with open("comps.pickle", "wb") as f:
                pickle.dump(self.final_companies, f, pickle.HIGHEST_PROTOCOL)


    def get_directors(self):
        with open("comps.pickle", "rb") as f:
            numbers = pickle.load(f)
        time.sleep(self.timeout)
        graph = {}
        while len(numbers) > 0:
            count = 0
            t_5mins = time.time() + self.timeout
            print("numbers left: ", len(numbers))
            while count < 600:
                if len(numbers) > 0:
                    c = numbers.pop()
                    count, directors = self.ch.get_dirs(c, count)
                    try:
                        if directors.status_code == 429:
                            count = 601
                            numbers.add(c)
                        else:
                            count, results = self.ch.get_name_guid(directors.json()["items"], count)
                            if len(results) > 0:
                                graph[c] = results
                    except KeyError:
                        print("Key error")
                        print(directors)
                        print(count)
                    except json.decoder.JSONDecodeError:
                        print("decoding error")
                        print(directors)
                        print(count)
                        time.sleep(self.timeout)
                        count = 1
                else:
                    break
            with open("Graph_" + str(len(numbers)), "w+") as f1:
                f1.write(str(graph))

            wait = 3 + (t_5mins - time.time())
            if wait > 0:
                time.sleep(wait)

        with open("company_dirs_dictionary.pickle", "wb") as f:
            pickle.dump(graph, f, pickle.HIGHEST_PROTOCOL)

        print("written sucessfully")
        print("size", len(graph.__sizeof__()))





companies = ["hsbc", "tesco", "giffgaff", "google",
             "hello internet", "facebook", "University College London",
             "Heathrow Airport", "food and wine", "asr", "mae", "tow", "fig", "man", "hip",
             "smith"]
m = Main(companies)
m.get_directors()
