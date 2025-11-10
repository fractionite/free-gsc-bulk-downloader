# GSC Bulk Data Downloader

A simple, efficient Python script to download Google Search Console performance data in bulk and save it as daily CSV files.

This script makes one API call per report type for an entire date range, then processes the results locally, making it highly efficient and avoiding API quota limits.

## Features

* Download data for multiple dimension combinations at once.
* Pulls data for an entire date range in a single request (per report).
* Automatically splits the results into separate CSV files, one for each day.
* Organizes saved CSVs into subfolders based on report type.
* Configured entirely via command-line arguments (no hardcoded values).

## Setup

### 1. Google Search Console API

You must enable the Search Console API in your Google Cloud project and create a service account.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Go to "APIs & Services" > "Library" and search for "Google Search Console API". Enable it.
4.  Go to "APIs & Services" > "Credentials".
5.  Click "Create Credentials" > "Service Account".
6.  Give it a name (e.g., "gsc-downloader") and click "Done".
7.  Find your new service account, click the "Actions" (⋮) icon > "Manage keys".
8.  Click "Add Key" > "Create new key". Choose **JSON** and download the file. Save this file (e.g., `my-service-account.json`) securely.

### 2. Grant Access in Search Console

The service account is an "email address". You must grant it permission to view your GSC property.

1.  Go to your [Google Search Console](https://search.google.com/search-console/) property.
2.  Go to "Settings" > "Users and permissions".
3.  Click "Add User".
4.  Paste the service account's email address (e.g., `gsc-downloader@my-project-123.iam.gserviceaccount.com`) from the JSON file.
5.  Set the permission to "**Viewer**" (or Restricted).
6.  Click "Add".

## Installation

1.  Clone this repository:
    `git clone https://github.com/fractionite/gsc-bulk-downloader.git`
2.  Navigate to the directory:
    `cd gsc-bulk-downloader`
3.  (Recommended) Create a virtual environment:
    `python -m venv venv`
    `source venv/bin/activate`  # On Windows: `venv\Scripts\activate`
4.  Install the required packages:
    `pip install -r requirements.txt`

## How to Run

Run the script from your terminal.

**Example:**

```bash
python download_gsc_data.py \
    --property "sc-domain:your-website.com" \
    --sa_file "path/to/your-service-account.json" \
    --start "2025-10-01" \
    --end "2025-10-31" \
    --output_dir "gcs_reports"
