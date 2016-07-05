import json, codecs
import os
import sys
import pages
from bs4 import BeautifulSoup
from settings import base_urls
from crawler import Crawler


MIRROR = 'archive/'


# Verifier superclass
class Verifier:
    def __init__(self):
        self.pages = []
        self.minimum_size = 0
        self.page_elements = {}
        self.failed_pages = []

    # Populate self.pages with the relevant files
    def harvest_pages(self, json_filename, json_list, url_end, page_class):
        """
        :param json_list: The list in the json file of found URLs
        :param url_end: The json_list is non segregated by page type
        :param page_class: The subclass for the specific page type
        :return: Null, but self.pages is populated.
        """
        for url in json_list:
            if url_end in url:
                print('rel: ', url)
                if url in json_filename['error_list']:
                    self.failed_pages.append(url)
                    print('error: ', url)
                else:
                    try:
                        obj = page_class(url)
                        self.pages.append(obj)
                    except FileNotFoundError:
                        self.failed_pages.append(url)
                json_list.remove(url)

            # First check

    # Compare page size to page-specific minimum that any fully-scraped page should have
    def size_comparison(self):
        for page in self.pages:
            # print(page)
            # print(page.file_size)
            if not page.file_size > self.minimum_size:
                print('Failed: size_comparison(): ', page, ' has size: ', page.file_size)
                self.failed_pages.append(page.url)
        return

    # Second check
    # Check that specified elements are present and non-empty in each page
    # Check that specified elements or their alternates are present and non-empty in each page
    # Alternate: different elements appear if there isn't supposed to be content, so it has to check both
    # Format: Filled-in : Alternate
    def spot_check(self):
        for page in self.pages:
            soup = page.get_content()
            for element in self.page_elements:
                alt = self.page_elements[element]
                result = soup.select(element)
                # No results or empty results
                if (len(result) == 0 or len(result[0].contents) == 0) and alt != '':
                    # print("Failed: first spot_check(): ", page, element, "Retrying with alt: ", alt)
                    alt_result = soup.select(alt)

                    # Element's alternate has no or empty results
                    if len(alt_result) == 0 or len(alt_result[0].contents) == 0:
                        print("Failed: alternate spot_check(): ", page, alt, '\n')
                        self.failed_pages.append(page.url)
                        break

                elif (len(result) == 0 or len(result[0].contents) == 0) and alt == '':
                    print('Failed: spot_check(): ', page, element, "No alt.", '\n')
                    self.failed_pages.append(page.url)
                    break

        return


# Verifier subclasses

class ProjectDashboardVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 410
        self.page_elements = {
            '#nodeTitleEditable': '',  # Title
            '#contributors span.date.node-last-modified-date': '',  # Last modified
            '#contributorsList > ol': '',  # Contributor list
            '#tb-tbody': '',  # File list
            '#render-node': 'div.row > div:nth-of-type(2) > div.components.panel.panel-default > div.panel-body > p',
            # Nodes list
            '#logScope > div > div > div.panel-body > span > dl': '#logFeed > div > p'
            # Activity / "Unable to retrieve at this time"
        }

    def run_verifier(self,json_filename, json_list):
        self.harvest_pages(json_filename, json_list, '', ProjectDashboardPage)
        self.size_comparison()
        self.spot_check()


class ProjectFilesVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 380
        self.page_elements = {
            '.fg-file-links': '',  # Links to files (names them)
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, 'files/', ProjectFilesPage)
        self.size_comparison()
        self.spot_check()


class ProjectWikiVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 410
        self.page_elements = {
            'pre': '#wikiViewRender > p > em',  # Wiki content / `No wiki content`
            '#viewVersionSelect option': '',  # Current version date modified
            '.fg-file-links': ''  # Links to other pages (names them)
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, 'wiki/', ProjectWikiPage)
        self.size_comparison()
        self.spot_check()


class ProjectAnalyticsVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 380
        self.page_elements = {
            '#adBlock': 'div.watermarked > div > div.m-b-md.p-md.osf-box-lt.box-round.text-center',
            # Warning about AdBlock
            'iframe': 'div.watermarked > div > div.m-b-md.p-md.osf-box-lt.box-round.text-center',
            # External frame for analytics
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, 'analytics/', ProjectAnalyticsPage)
        self.size_comparison()
        self.spot_check()


class ProjectRegistrationsVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 390
        self.page_elements = {
            '#renderNode': '#registrations > div > div > p'  # List of nodes
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, 'registrations/', ProjectRegistrationsPage)
        self.size_comparison()
        self.spot_check()


class ProjectForksVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 380
        self.page_elements = {
            '#renderNode': 'div.watermarked > div > div.row > div.col-xs-9.col-sm-8 > p'  # List
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, 'forks/', ProjectForksPage)
        self.size_comparison()
        self.spot_check()


class RegistrationDashboardVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 410
        self.page_elements = {
            '#nodeTitleEditable': '',  # Title
            '#contributors > div > p:nth-of-type(5) > span': '',  # Last modified
            '#contributorsList > ol': '',  # Contributor list
            '#tb-tbody': '',  # File list
            '#render-node': 'div.row > div:nth-of-type(2) > div.components.panel.panel-default > div.panel-body > p',
            # Nodes list
            '#logScope > div > div > div.panel-body > span > dl': '#logFeed > div > p'
            # Activity / "Unable to retrieve at this time"
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, '', RegistrationDashboardPage)
        self.size_comparison()
        self.spot_check()


class RegistrationFilesVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 380
        self.page_elements = {
            '.fg-file-links': '',  # Links to files (names them)
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, 'files/', RegistrationFilesPage)
        self.size_comparison()
        self.spot_check()


class RegistrationWikiVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 410
        self.page_elements = {
            'pre': '#wikiViewRender > p > em',  # Wiki content / `No wiki content`
            '#viewVersionSelect option': '',  # Current version date modified
            '.fg-file-links': ''  # Links to other pages (names them)
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, 'wiki/', RegistrationWikiPage)
        self.size_comparison()
        self.spot_check()


class RegistrationAnalyticsVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 380
        self.page_elements = {
            '#adBlock': 'div.watermarked > div > div.m-b-md.p-md.osf-box-lt.box-round.text-center',
            # Warning about AdBlock
            'iframe': 'div.watermarked > div > div.m-b-md.p-md.osf-box-lt.box-round.text-center',
            # External frame for analytics
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, 'analytics/', RegistrationAnalyticsPage)
        self.size_comparison()
        self.spot_check()


class RegistrationForksVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 380
        self.page_elements = {
            '#renderNode': 'div.watermarked > div > div.row > div.col-xs-9.col-sm-8 > p'  # List
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, 'forks/', RegistrationForksPage)
        self.size_comparison()
        self.spot_check()


class UserProfileVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 80
        self.page_elements = {
            '#projects': 'div > div:nth-of-type(1) > div > div.panel-body > div',  # Project list / "No projects"
            '#components': 'div > div:nth-of-type(2) > div > div.panel-body > div',  # Component list / "No components"
            'body h2': ''  # Activity points, project count
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, '', UserProfilePage)
        self.size_comparison()
        self.spot_check()


class InstitutionDashboardVerifier(Verifier):
    def __init__(self):
        Verifier.__init__(self)
        self.minimum_size = 350
        self.page_elements = {
            '#fileBrowser > div.db-infobar > div > div': '#fileBrowser > div.db-infobar > div > div',  # Project preview
            '#tb-tbody': '#fileBrowser > div.db-main > div.db-non-load-template.m-md.p-md.osf-box'  # Project browser
        }

    def run_verifier(self, json_filename, json_list):
        self.harvest_pages(json_filename, json_list, '', InstitutionDashboardPage)
        self.size_comparison()
        self.spot_check()


# called when json file had scrape_nodes = true
# checks for all the components of a project and if they were scraped
# verifies them and returns a list of the failed pages
def scraped_nodes(verification_dictionary, list_name):
    nodes_list_verified = []
    if verification_dictionary['include_files']:
        project_files_verifier = ProjectFilesVerifier()
        project_files_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
        project_files = project_files_verifier.failed_pages
        nodes_list_verified += project_files
    if verification_dictionary['include_wiki']:
        project_wiki_verifier = ProjectWikiVerifier()
        project_wiki_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
        project_wiki = project_wiki_verifier.failed_pages
        nodes_list_verified += project_wiki
    if verification_dictionary['include_analytics']:
        project_analytics_verifier = ProjectAnalyticsVerifier()
        project_analytics_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
        project_analytics = project_analytics_verifier.failed_pages
        nodes_list_verified += project_analytics
    if verification_dictionary['include_registrations']:
        project_registrations_verifier = ProjectRegistrationsVerifier()
        project_registrations_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
        project_registrations = project_registrations_verifier.failed_pages
        nodes_list_verified += project_registrations
    if verification_dictionary['include_forks']:
        project_forks_verifier = ProjectForksVerifier()
        project_forks_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
        project_forks = project_forks_verifier.failed_pages
        nodes_list_verified += project_forks
    if verification_dictionary['include_dashboard']:  # This must go last because its URLs don't have a specific ending.
        project_dashboards_verifier = ProjectDashboardVerifier()
        project_dashboards_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
        project_dashboards = project_dashboards_verifier.failed_pages
        nodes_list_verified += project_dashboards
    return nodes_list_verified


# called when json file had scrape_registrations = true
# verifies the components of a registration and returns a list of the failed pages
def scraped_registrations(verification_dictionary, list_name):
    # Must run all page types automatically
    registration_files_verifier = RegistrationFilesVerifier()
    registration_files_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
    registration_files = registration_files_verifier.failed_pages

    registration_wiki_verifier = RegistrationWikiVerifier()
    registration_wiki_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
    registration_wiki = registration_wiki_verifier.failed_pages

    registration_analytics_verifier = RegistrationAnalyticsVerifier()
    registration_analytics_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
    registration_analytics = registration_analytics_verifier.failed_pages

    registration_forks_verifier = RegistrationForksVerifier()
    registration_forks_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
    registration_forks = registration_forks_verifier.failed_pages

    registration_dashboards_verifier = RegistrationDashboardVerifier()
    registration_dashboards_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
    registration_dashboards = registration_dashboards_verifier.failed_pages

    registrations_list_verified = registration_files + registration_wiki + registration_analytics + \
        registration_forks + registration_dashboards
    return registrations_list_verified


# called when json file had scrape_users = true
# verifies all user profile pages and returns a list of the failed pages
def scraped_users(verification_dictionary, list_name):
    user_profiles_verifier = UserProfileVerifier()
    user_profiles_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
    user_profiles = user_profiles_verifier.failed_pages
    return user_profiles


# called when json file had scrape_institutions = true
# verifies all user profile pages and returns a list of the failed pages
def scraped_institutions(verification_dictionary, list_name):
    institution_dashboards_verifier = InstitutionDashboardVerifier()
    institution_dashboards_verifier.run_verifier(verification_dictionary, verification_dictionary[list_name])
    institution_dashboards = institution_dashboards_verifier.failed_pages
    return institution_dashboards


def call_rescrape(json_filename, verification_json_filename):
    second_chance = Crawler()
    if json_filename['scrape_nodes']:
        second_chance.node_urls = verification_json_filename['node_urls_failed_verification']
        second_chance.scrape_nodes()
    if json_filename['scrape_registrations']:
        second_chance.registration_urls = verification_json_filename['registration_urls_failed_verification']
    if json_filename['scrape_users']:
        second_chance.user_profile_page_urls = verification_json_filename['user_profile_page_urls_failed_verification']
    if json_filename['scrape_institutions']:
        second_chance.institution_urls = verification_json_filename['institution_urls_failed_verification']


# first verification and then scraping the failed pages
def initial_verification(json_file):
    with codecs.open(json_file, mode='r', encoding='utf-8') as failure_file:
        run_info = json.load(failure_file)
    with codecs.open(json_file, mode='r', encoding='utf-8') as failure_file:
        run_copy = json.load(failure_file)
    if run_info['scrape_finished']:
        if run_info['scrape_nodes']:
            run_copy['node_urls_failed_verification'] = scraped_nodes(run_info, 'node_urls')
        if run_info['scrape_registrations']:
            run_copy['registration_urls_failed_verification'] = scraped_registrations(run_info, 'registration_urls')
        if run_info['scrape_users']:
            run_copy['user_profile_page_urls_failed_verification'] = scraped_registrations(run_info,
                                                                                           'user_profile_page_urls')
        if run_info['scrape_institutions']:
            run_copy['institution_urls_failed_verification'] = scraped_institutions(run_info, 'institution_urls')

        with codecs.open(json_file, mode='w', encoding='utf-8') as file:
            json.dump(run_copy, file, indent=4)

    call_rescrape(run_info, run_copy)

    return run_copy


def subsequent_verifications(json_file, verified_dictionary, num_retries):
    if verified_dictionary['scrape_finished']:
        for i in range(num_retries):
            if verified_dictionary['scrape_nodes']:
                verified_dictionary['node_urls_failed_verification'] = scraped_nodes(verified_dictionary,
                                                                                     'node_urls_failed_verification')
            if verified_dictionary['scrape_registrations']:
                verified_dictionary['registration_urls_failed_verification'] = \
                    scraped_registrations(verified_dictionary, 'registration_urls_failed_verification')
            if verified_dictionary['scrape_users']:
                verified_dictionary['user_profile_page_urls_failed_verification'] = \
                    scraped_users(verified_dictionary, 'user_profile_page_urls_failed_verification')
            if verified_dictionary['scrape_institutions']:
                verified_dictionary['institution_urls_failed_verification'] = \
                    scraped_institutions(verified_dictionary, 'institution_urls_failed_verification')
            # truncates json and dumps new lists
            with codecs.open(json_file, mode='w', encoding='utf-8') as file:
                json.dump(verified_dictionary, file, indent=4)

            call_rescrape(verified_dictionary, verified_dictionary)


def main(json_filename, num_retries):
    # call two verification/scraping methods depending on num retries
    if num_retries > 1:
        run_file = initial_verification(json_filename)
        subsequent_verifications(json_filename, run_file, num_retries)
    if num_retries == 1:
        initial_verification(json_filename)
