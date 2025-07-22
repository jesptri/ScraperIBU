from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from time import sleep
import pandas as pd
import re

from api_biathlon import *

class BiathlonScraper:
    def __init__(self, race_competition, race_location, race_type, race_season):
        self.race_competition = race_competition
        self.race_location = race_location
        self.race_type = race_type
        self.race_season = race_season
        self.driver = None
        self.df_final = pd.DataFrame(columns=['Ranking', 'Bib', 'Name', 'Country'])

    def time_data_to_excel(self):
        self.driver = self._init_driver()
        self._click_button_and_cookies()
        self._select_year()
        self._click_race_competition()
        self._click_race_location()
        self._click_relive()
        self._click_reload_live_data()
        
        split_time_list = self._get_list_of_split_time()
        nombre_etapes = len(split_time_list) + 4
        yield int(100*4/nombre_etapes)
        
        places = get_places(RT, self.race_season, self.race_competition)
        code_place = places[self.race_location]
        all_races_code1 = get_races(RT, code_place)
        race_id = get_key_from_value(all_races_code1, self.race_type)
        
        bib_name_nat, _, _ = get_bib_name_nat_list(RT, race_id)

        for i in range(0, len(split_time_list)-1):
            print(f"Scraping starts for {split_time_list[i]}")
            self._process_split_time(split_time_list[i], split_time_list, i, bib_name_nat)
            print(f"End scrap {split_time_list[i]}")
            yield int(100*(4+i)/nombre_etapes)
            
        self._final_modifications()

    def _init_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://biathlonresults.com/#/datacenter")
        driver.maximize_window()
        return driver

    def _is_pursuit(self):
        return "Pursuit" in self.race_type.split(" ")

    def _get_current_season(self):
        seasonItem = self.driver.find_element(By.CSS_SELECTOR,'prevnext-selector[displayfield = "Description"]')
        textHtml = seasonItem.get_attribute('innerHTML')
        yearWebObject = re.search('\d{4}/\d{4}', textHtml)
        if yearWebObject:
            yearWeb = yearWebObject.group().split('/')[0]
        else:
            raise ValueError('Current year not found')
        return int(yearWeb)

    def _select_year(self):
        annee_1_course = int(self.race_season.split("-")[0])
        annee_1_site = self._get_current_season()
        number_of_clicks = annee_1_site - annee_1_course

        title_right = self.driver.find_element(By.CSS_SELECTOR,'span[slot = "title-right"]')
        competition_schedule_header = title_right.find_element(By.CSS_SELECTOR,'competition-schedule-header[class = "au-target"]')
        prevnext_selector = competition_schedule_header.find_element(By.CSS_SELECTOR, 'prevnext-selector[displayfield = "Description"]')
        left_arrow = prevnext_selector.find_element(By.XPATH, './/span[@class = "au-target"]//i[@class = "fa fa-arrow-circle-left"]')
        
        for _ in range(number_of_clicks):
            if number_of_clicks > 0:
                left_arrow.click()

    def _click_race_type(self, lieu):
        if self.race_competition != "JUNIOR":
            parent_div = WebDriverWait(lieu, 10).until(EC.visibility_of_element_located((By.XPATH, "./ancestor::div[3]")))   
            
            try:
                listes_courses_k = parent_div.find_element(By.XPATH, "./descendant::div[@class='au-target panel-collapse collapse in']")
            except:
                listes_courses_k = parent_div.find_element(By.XPATH, "./descendant::div[@class='au-target panel-collapse collapse']")

            listes_courses_1 = listes_courses_k.find_element(By.XPATH, "./descendant::div[@class='list-group']")
            listes_courses_2 = listes_courses_1.find_elements(By.XPATH, ".//a")

            for course in listes_courses_2:                
                course_0 = course.find_element(By.XPATH, ".//table[@class='stdTable']")
                course_1 = course_0.find_element(By.XPATH, "./descendant::tr[@class='stRow']")
                course_2 = course_1.find_element(By.XPATH, "./td[2]")

                if self.race_type == course_2.text:
                    course_2.click()
                    break

    def _click_race_competition(self):
        if self.race_competition == "IBU CUP":
            ibu = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#dbSchedule2']")))
            ibu.click()
        elif self.race_competition == "JUNIOR":
            ibu = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#dbSchedule2']")))
            ibu.click()
            ibu.click()
        sleep(2)

    def _click_race_location(self):
        lieu = WebDriverWait(self.driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{self.race_location}')]")))
        lieu.click()
        
        try:            
            self._click_race_type(lieu)
        except:
            lieu.click()
            self._click_race_type(lieu)
        
        sleep(3)

    def _get_list_of_split_time(self):
        STstart = self.driver.find_elements(
            By.XPATH, 
            "//div[@class='bladeInnerContainer au-target']//div[@class='content au-target']//div[@class='rowContainer menu-blade au-target']//div[@class='row']//div[@class='au-target panel panel-default']"
        )
        split_time_and_intermediates_container = [element.text for element in STstart if "INTERMEDIATES" in element.text]
        
        try:
            split_time_list = split_time_and_intermediates_container[0].split("\n")[1:] + ["Pour pas que ça bug"]
        except:
            split_time_list = split_time_and_intermediates_container.split("\n")[1:] + ["Pour pas que ça bug"]
            print("ça passe ici !")
            
        return split_time_list

    def _get_biathletes_lines(self):
        resulttable = self.driver.find_element(By.XPATH, "//div[@class = 'rtBody scrollable-resultTable au-target']")    
        table_intermediaire = resulttable.find_element(By.XPATH, "./div[@class = 'au-target']")    
        return table_intermediaire.find_elements(By.XPATH, './div')

    def _get_data(self):
        all_data = []
        for scroll_number in range(0,4):
            if scroll_number != 0:
                scrollable_section = self.driver.find_element(
                    By.XPATH,"//div[@class='rtBody scrollable-resultTable au-target']"
                )
                self.driver.execute_script("arguments[0].scrollBy(0, 550);", scrollable_section)
            
            data = []
            biathlete_lines = self._get_biathletes_lines()
            for biathlete_line in biathlete_lines:
                try:
                    biathlete_line_text = biathlete_line.text
                    data.append([biathlete_line_text])
                except:
                    pass
            all_data += data
        return all_data

    def _click_relive(self):
        relive = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'RE-LIVE')]")))
        relive.click()

    def _click_reload_live_data(self):
        reload_live_data = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'RE-LOAD LIVE DATA')]")))
        reload_live_data.click()    
        sleep(8)

    def _click_button_and_cookies(self):
        button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'CONTINUE WITHOUT REGISTRATION')]")))
        button.click()
        
        try:
            cookies = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[text()='OK']")))
            cookies.click()
        except TimeoutException:
            pass
        
        sleep(1)

    def _delete_duplicate_items(self, data_list):
        return list(dict.fromkeys(data_list))

    def _get_split_time_for_driver(self, split_time):
        return WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[text()='{split_time}']")))

    def _delete_badly_formatted_data(self, final_data, split_time_list, i):
        for data in final_data:
            if 'DNF' in data or 'LAP' in data or 'DSQ' in data:
                final_data.remove(data) 
            else:
                data[0] = int(data[0])
                data[1] = int(data[1])
                if len(data) == 5:
                    data[4] = data[4].replace("'","").replace("+","")
                elif len(data) == 6:
                    if "+" in data[4]:
                        data[4] = data[4].replace("'","").replace("+","")
                    if "+" or ":" in data[5]:
                        data[5] = data[5].replace("'","").replace("+","")
                        data.remove(data[4])
                elif len(data) == 7:
                    data.remove(data[2])
                    data.remove(data[-2])
                    
        for data in final_data:
            if len(data) != 5:
                if type(data[4]) == int or ":" in data[5]:
                    if ":" in data[5] and "+" in data[5]:
                        data[5] = data[5].replace("+", "")
                    data.remove(data[4])

        new_good_data = pd.DataFrame(final_data)
        
        if len(new_good_data.columns) == 7:
            new_good_data.drop(new_good_data.columns[6], axis=1, inplace=True)        
        elif len(new_good_data.columns) == 6:
            new_good_data.drop(new_good_data.columns[5], axis=1, inplace=True)

        try:
            new_good_data.drop(new_good_data.index[-1] and new_good_data.index[-2], inplace=True)
        except:
            pass

        if new_good_data.shape[1] == 5:
            new_good_data.columns = ['Ranking', 'Bib', 'Name', 'Country', split_time_list[i]]
        elif new_good_data.shape[1] == 6:
            new_good_data = new_good_data.iloc[:, :-1]    
            new_good_data.columns = ['Ranking', 'Bib', 'Name', 'Country', split_time_list[i]]
            
        new_good_data['Name'] = new_good_data["Country"] + " " + new_good_data["Name"]
                        
        return new_good_data

    def _convert_time_data_to_good_format(self, new_good_data, split_time_list, i):
        new_good_data['Ranking'] = pd.to_numeric(new_good_data['Ranking'], errors='coerce')
        new_good_data.sort_values(by='Ranking', inplace=True)  
        new_good_data.drop_duplicates(inplace=True)     
                        
        new_good_data[split_time_list[i]] = new_good_data[split_time_list[i]].apply(convert_chrono_to_seconds)
        new_good_data.drop_duplicates(inplace=True) 
        temps_leader = new_good_data.at[new_good_data.index[0], split_time_list[i]]

        for index, row in new_good_data.iterrows():
            if index == new_good_data.index[0] or row[-1] == temps_leader: 
                new_good_data.at[index, split_time_list[i]] = temps_leader
            else:
                new_good_data.at[index, split_time_list[i]] += temps_leader

    def _manage_composed_family_name(self, deduplicated_data):
        donnees_csv_int = [[element[0].split(' ')][0] for element in deduplicated_data]
        
        for element in donnees_csv_int:
            if len(element) > 4:
                if element[3].isupper() and element[4].isupper():
                    element[3] = element[3] + " " + element[4]
                    element.pop(4)
        
        return [mot for mot in donnees_csv_int if len(mot) >= 5]

    def _convert_bib_to_int(self, new_good_data):
        for index, row in new_good_data.iterrows():
            try:
                new_good_data.at[index, 'Bib'] = int(row['Bib'])
            except ValueError:
                new_good_data.at[index, 'Bib'] = 0

    def _build_df_final(self, new_good_data, split_time_list, i):
        if i == 0:
            self.df_final["Bib"] = new_good_data["Bib"]
            self.df_final["Name"] = new_good_data["Name"]
            self.df_final["Country"] = new_good_data["Country"]
            self.df_final.sort_values(by='Bib', inplace=True)
        
        self.df_final[split_time_list[i]] = new_good_data[split_time_list[i]]

    def _process_split_time(self, split_time, split_time_list, i, bib_name_nat):
        split_time_for_driver = self._get_split_time_for_driver(split_time)
        split_time_for_driver.click()
        
        duplicated_data = self._get_data()
        split_time_for_driver.click()

        deduplicated_data = self._delete_duplicate_items(duplicated_data)
        final_data = self._manage_composed_family_name(deduplicated_data)
        
        new_good_data = self._delete_badly_formatted_data(final_data, split_time_list, i)
        self._fix_frequent_bug_with_names(new_good_data, bib_name_nat)

        new_good_data = new_good_data.dropna()
        new_good_data = new_good_data.iloc[:-1]
    
        self._convert_bib_to_int(new_good_data)
        self._convert_time_data_to_good_format(new_good_data, split_time_list, i)
                      
        new_good_data.sort_values(by='Bib', inplace=True)
        new_good_data.reset_index(inplace=True, drop=True)
        
        self._build_df_final(new_good_data, split_time_list, i)

    def _fix_frequent_bug_with_names(self, new_good_data, bib_name_nat):
        for index, row in new_good_data.iterrows():
            try:
                bib = int(row['Bib'])
                if bib in bib_name_nat:
                    new_good_data.at[index, 'Name'] = bib_name_nat[bib]
            except ValueError:
                continue

    def _final_modifications(self):
        self.df_final.sort_values(by='Bib', inplace=True)
        self.df_final.reset_index(inplace=True, drop=True)

# Usage example:
scraper = BiathlonScraper("WORLD CUP", "Lenzerheide (SUI)", "Women 10km Sprint", "2023-2024")
for progress in scraper.time_data_to_excel():
    print(f"Progress: {progress}%")