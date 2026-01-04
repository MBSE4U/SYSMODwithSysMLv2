
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add api folder to path
sys.path.append(os.path.join(os.getcwd(), 'api'))

import sysmod_api_helpers

class TestCaching(unittest.TestCase):
    
    def setUp(self):
        # Reset cache before each test
        sysmod_api_helpers.ELEMENT_CACHE = {}
        self.server_url = "http://mock-server"
        self.project_id = "proj1"
        self.commit_id = "commit1"
        self.commit_url = f"{self.server_url}/projects/{self.project_id}/commits/{self.commit_id}"
        
    @patch('sysmod_api_helpers.session')
    def test_load_cache(self, mock_session):
        # Mock Response for bulk elements
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"@id": "el1", "name": "Element 1"},
            {"@id": "el2", "name": "Element 2"}
        ]
        mock_session.get.return_value = mock_response
        
        # Test loading
        count = sysmod_api_helpers.load_model_cache(self.server_url, self.project_id, self.commit_id)
        
        self.assertEqual(count, 2)
        self.assertIn(self.commit_url, sysmod_api_helpers.ELEMENT_CACHE)
        self.assertEqual(sysmod_api_helpers.ELEMENT_CACHE[self.commit_url]['el1']['name'], "Element 1")
        
        # Verify URL called
        mock_session.get.assert_called_with(f"{self.commit_url}/elements")

    @patch('sysmod_api_helpers.session')
    def test_get_element_from_cache(self, mock_session):
        # Pre-load cache manually
        sysmod_api_helpers.ELEMENT_CACHE[self.commit_url] = {
            "el1": {"@id": "el1", "name": "Cached Element"}
        }
        
        # Call get_element_fromAPI
        element = sysmod_api_helpers.get_element_fromAPI(self.commit_url, "el1")
        
        self.assertEqual(element['name'], "Cached Element")
        # Ensure session.get was NOT called
        mock_session.get.assert_not_called()

    @patch('sysmod_api_helpers.session')
    def test_get_element_cache_miss(self, mock_session):
        # Cache exists but element is missing
        sysmod_api_helpers.ELEMENT_CACHE[self.commit_url] = {
            "el1": {"@id": "el1", "name": "Cached Element"}
        }
        
        # Mock network response for fallback
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"@id": "el2", "name": "Network Element"}
        mock_session.get.return_value = mock_response
        
        # Call get_element_fromAPI for el2
        element = sysmod_api_helpers.get_element_fromAPI(self.commit_url, "el2")
        
        self.assertEqual(element['name'], "Network Element")
        # Ensure session.get WAS called
        mock_session.get.assert_called()

        self.assertEqual(element['name'], "Network Element")
        # Ensure session.get WAS called
        mock_session.get.assert_called()

    @patch('sysmod_api_helpers.session')
    def test_query_api_by_kind(self, mock_session):
        # Pre-load cache
        sysmod_api_helpers.ELEMENT_CACHE[self.commit_url] = {
            "el1": {"@id": "el1", "@type": "Class", "name": "Class 1 in Cache"},
        }
        
        # Test Query by Kind - Should hit Network
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"@id": "el2", "@type": "Class", "name": "Class 2 from Network"}]
        mock_session.post.return_value = mock_response

        results = sysmod_api_helpers.get_elements_byKind_fromAPI(self.server_url, self.project_id, self.commit_id, "Class")
        
        # Should return network results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Class 2 from Network")
        
        # Ensure session.post WAS called
        mock_session.post.assert_called()

if __name__ == '__main__':
    unittest.main()
