#!/usr/bin/python
import os
import datetime
import pandas as pd
import argparse
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError

class SearchConsoleAPI:
    """
    A class to interact with the Google Search Console API.
    
    Manages authentication, data retrieval, and conversion to pandas DataFrames.
    """
    def __init__(self, service_account_file: str, scopes: list):
        """
        Initializes the SearchConsoleAPI instance.
        
        Args:
            service_account_file (str): Path to the service account key JSON file.
            scopes (list): A list of API scopes.
        """
        self.service_account_file = service_account_file
        self.scopes = scopes
        self.service = self._authenticate()
        
    def _authenticate(self):
        """Authenticates with the Search Console API using a service account."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=self.scopes
            )
            return build('searchconsole', 'v1', credentials=credentials)
        except FileNotFoundError:
            print(f"Error: The service account key file was not found at '{self.service_account_file}'.")
            print("Please ensure the path is correct and the file exists.")
            return None
        except Exception as e:
            print(f"An error occurred during authentication: {e}")
            return None

    def execute_request(self, property_uri: str, start_date: str, end_date: str, dimensions: list, row_limit: int = 25000):
        """
        Executes a searchanalytics.query request and returns a pandas DataFrame.
        
        Args:
            property_uri (str): The Search Console property URI.
            start_date (str): The start date for the query (YYYY-MM-DD).
            end_date (str): The end date for the query (YYYY-MM-DD).
            dimensions (list): The list of dimensions to group by (e.g., ['page', 'query']).
            row_limit (int): The maximum number of rows to return. Max 25,000.
            
        Returns:
            pd.DataFrame: A DataFrame containing the query results, or an empty DataFrame if the request fails.
        """
        if not self.service:
            print("API service is not initialized. Check authentication.")
            return pd.DataFrame()
        
        # Add 'date' to dimensions to get daily data
        if 'date' not in dimensions:
            dimensions.append('date')
            
        request_body = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': dimensions,
            'rowLimit': row_limit,
            'startRow': 0
        }
        
        try:
            response = self.service.searchanalytics().query(
                siteUrl=property_uri, body=request_body
            ).execute()
            
            if 'rows' not in response:
                print(f"No data found for dimensions: {dimensions} from {start_date} to {end_date}")
                return pd.DataFrame()

            df = pd.DataFrame(response['rows'])
            
            # The 'keys' column needs to be split into separate columns based on dimensions
            # We must use the *original* dimensions list from the request body
            df[request_body['dimensions']] = pd.DataFrame(df['keys'].tolist(), index=df.index)
            df.drop(columns=['keys'], inplace=True)
            
            return df
            
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            print(f"Error content: {e.content}")
            return pd.DataFrame()
        except Exception as e:
            print(f"An error occurred executing the request: {e}")
            return pd.DataFrame()

def save_daily_csvs(df: pd.DataFrame, report_type: str, base_dir: str):
    """
    Takes a DataFrame with a 'date' column and saves a separate CSV for each date.
    """
    if 'date' not in df.columns:
        print(f"Error: 'date' column not found for {report_type}. Cannot split by date.")
        return

    # Group by the 'date' column
    grouped = df.groupby('date')
    
    print(f"Splitting '{report_type}' data into {len(grouped)} daily files...")
    
    for date_str, daily_df in grouped:
        try:
            # Parse the date string to create a date object for formatting
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            
            dir_path = os.path.join(base_dir, report_type)
            os.makedirs(dir_path, exist_ok=True)
            
            file_name = f"{report_type}_{date_obj.strftime('%Y-%m-%d')}.csv"
            file_path = os.path.join(dir_path, file_name)
            
            daily_df.to_csv(file_path, index=False)
            
        except ValueError:
            print(f"Skipping group with invalid date format: {date_str}")
        except Exception as e:
            print(f"Could not save file for date {date_str}: {e}")
    
    print(f"Successfully saved daily files for '{report_type}' to '{base_dir}/{report_type}/'")


def main():
    parser = argparse.ArgumentParser(description="Download Google Search Console data into daily CSV files.")
    parser.add_argument('--property', required=True, help="Your GSC Property URI (e.g., 'sc-domain:example.com')")
    parser.add_argument('--sa_file', required=True, help="Path to your service account JSON key file.")
    parser.add_argument('--start', required=True, help="Start date in YYYY-MM-DD format.")
    parser.add_argument('--end', required=True, help="End date in YYYY-MM-DD format.")
    parser.add_argument('--output_dir', default='search_console_reports', help="Directory to save the CSV reports (default: 'search_console_reports')")
    parser.add_argument('--limit', type=int, default=25000, help="Row limit per API request (max: 25000)")
    
    args = parser.parse_args()
    
    # Configuration
    SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
    
    # Define the different report types with their dimensions
    reports_to_run = {
        'page_query_country_device': ['page', 'query', 'country', 'device'],
        'search_appearance': ['searchAppearance'],
        'query_page': ['query', 'page'],
        'page': ['page'],
        'query': ['query'],
        'country': ['country'],
        'device': ['device'],
    }

    # Initialize the API client
    sc_api = SearchConsoleAPI(args.sa_file, SCOPES)
    
    if not sc_api.service:
        print("Failed to initialize API. Exiting.")
        return

    # Loop through each report type (NOT each date)
    for report_name, dimensions_list in reports_to_run.items():
        print(f"--- Fetching '{report_name}' data from {args.start} to {args.end} ---")
        
        # Make ONE API request for the entire date range
        df = sc_api.execute_request(
            property_uri=args.property,
            start_date=args.start,
            end_date=args.end,
            dimensions=dimensions_list.copy(),  # Pass a copy
            row_limit=args.limit
        )
        
        # Save the resulting (large) DataFrame
        if not df.empty:
            save_daily_csvs(df, report_name, args.output_dir)
        else:
            print(f"No data returned for '{report_name}'.")

# Main execution block
if __name__ == '__main__':
    main()
