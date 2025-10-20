from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import json


def pandify_course_data(soup, url):
    course_data = {}

    # Extract year
    year_tag = soup.find(
        "span", id="ctl00_ctl00_cphGeneral_cphMain_lblAcademiejaarOmschrijving"
    )
    course_data["year"] = year_tag.text.strip() if year_tag else None

    # Extract faculty
    faculty_tag = soup.find("u", string=re.compile(r"Komt voor in"))
    if faculty_tag:
        faculty_list = faculty_tag.find_next("ul")
        if faculty_list:
            faculties = []
            for li in faculty_list.find_all("li", recursive=False):
                for div in li.find_all("div"):
                    div.decompose()
                faculties.append(li.text.strip())
            course_data["faculties"] = faculties

    # Extract course title
    title_tag = soup.find("h2", id="ctl00_ctl00_cphGeneral_cphMain_dStudiegidsTitle")
    course_data["title"] = title_tag.text.strip() if title_tag else None

    # Extract course code
    course_data["code"] = re.search(r"a=(\d+)&", url).group(1)

    # Extract credits
    credits_tag = soup.find(
        "span", id="ctl00_ctl00_cphGeneral_cphMain_lblInhoudStudieomvang"
    )
    course_data["credits"] = credits_tag.text.strip() if credits_tag else None

    # Extract all evaluation tables under h4 tags with text "Evaluatie"
    eval_tag = soup.find("h4", string="Evaluatie")
    if eval_tag:
        all_eval_data = []
        # Find all tables that follow this h4 tag until the next h4 or major element
        tables = eval_tag.find_all_next("table")
        for table in tables:
            eval_data = []
            for row in table.find_all("tr")[1:]:  # Skip header row
                cols = row.find_all("td")
                if len(cols) >= 3:  # Ensure there are enough columns
                    moment = cols[0].text.strip()
                    format = cols[1].text.strip()
                    percentage = cols[2].text.strip()
                    eval_data.append(
                        {
                            "moment": moment,
                            "format": format,
                            "percentage": percentage,
                        }
                    )
            if eval_data:
                all_eval_data.append(eval_data)

        if all_eval_data:
            course_data["evaluation_methods"] = all_eval_data
        # If no tables found, extract all text under the div following the eval_tag
        else:
            eval_div = eval_tag.find_next("div")
            if eval_div:
                course_data["evaluation_methods"] = eval_div.text.strip()

    # Extract if 2nd chance is available, after the span with text "Tweede examenkans:"
    second_chance_tag = soup.find("span", string="Tweede examenkans: ")
    if second_chance_tag:
        second_chance_value = second_chance_tag.find_next("span")
        course_data["second_chance"] = (
            second_chance_value.text.strip() if second_chance_value else None
        )

    # Convert to DataFrame
    df = pd.DataFrame([course_data])
    return df


def fetch_course_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to load page {url}")
    elif "Studiegids niet beschikbaar" in response.text:
        print(f"Course not available at {url}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")

    df = pandify_course_data(soup, url)

    return df


if __name__ == "__main__":
    data = pd.DataFrame()
    for course_id in range(189483, 203000):  # 189483 - 203000
        print(f"Fetching course ID: {course_id}")
        data = pd.concat(
            [
                data,
                fetch_course_data(
                    f"https://bamaflexweb.hogent.be/BMFUIDetailxOLOD.aspx?a={course_id}&b=5&c=1"
                ),
            ]
        )

    data.to_csv("./data/courses.csv", index=False)
    print("Data saved to courses.csv")
