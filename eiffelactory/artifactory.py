"""
Module for querying Artifactory to confirm the presence of the artifacts from
the received Eiffel ArtC events.
"""
import logging

import requests
from requests.auth import HTTPBasicAuth
from kombu.utils import json


class ArtifactoryConnection:
    def __init__(self, artifactory_config):
        self.AQL_DOMAIN_SEARCH_STRING = artifactory_config.aql_search_string
        self.ARTIFACTORY_SEARCH_URL = artifactory_config.url + '/api/search/aql/'
        self.artifacts_logger = logging.getLogger('artifacts')
        self.app_logger = logging.getLogger('app')
        self.username = artifactory_config.username
        self.password = artifactory_config.password

    def _format_aql_query(self, artifact_filename, build_path_substring):
        return self.AQL_DOMAIN_SEARCH_STRING.format(
            artifact_name=artifact_filename,
            build_path_substring=build_path_substring).replace('\n', '')

    def _execute_aql_query(self, query_string):
        response = requests.post(self.ARTIFACTORY_SEARCH_URL,
                                 auth=HTTPBasicAuth(self.username,
                                                    self.password),
                                 data=query_string)
        content = response.content.decode('utf-8')
        if response.status_code == 200:
            return content
        self.app_logger.error("Artifactory error: %d, %s",
                              response.status_code, content)
        return None

    def find_artifact_on_artifactory(self, artifact_filename, build_path_substring):
        """
        Queries Artifactory for the artifact, using the filename and the path
        substring from the purl, where it tries to match it with the build url
        present on Artifactory
        :param artifact_filename: tuple: the artifact filename
        :param build_path_substring: the substring from the build path
        :return:
        """
        query_string = self._format_aql_query(artifact_filename,
                                              build_path_substring)
        self.artifacts_logger.debug(query_string)

        content = self._execute_aql_query(query_string)

        if content:
            json_content = json.loads(content)
            results = json_content['results']
            return results
        return None
