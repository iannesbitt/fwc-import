## figshare-import
*Import and convert Figshare data and records to a DataONE repository*

- **Authors**: Nesbitt, Ian ([http://orcid.org/0000-0001-5828-6070](http://orcid.org/0000-0001-5828-6070))
- **License**: [Apache 2](http://opensource.org/licenses/Apache-2.0)
- [Package source code on GitHub](https://github.com/DataONEorg/figshare-import)
- [**Submit Bugs and feature requests**](https://github.com/DataONEorg/figshare-import/issues)
- Contact us: support@dataone.org
- [DataONE discussions](https://github.com/DataONEorg/dataone/discussions)

This software is meant to provide transport of data and translation of metadata from Figshare's json format to DataONE. It uses a custom translation method to convert to Ecological Metadata Language (EML) and upload data, metadata and resource maps to a DataONE Metacat instance. This workflow may be run during repository setup to move a large corpus from Figshare into a new DataONE repository.

DataONE in general, and figshare-import in particular, are open source, community projects.  We [welcome contributions](./CONTRIBUTING.md) in many forms, including code, graphics, documentation, bug reports, testing, etc.  Use the [DataONE discussions](https://github.com/DataONEorg/dataone/discussions) to discuss these contributions with us.


## Documentation

Documentation is a work in progress. All functions have reStructuredText docstrings and fairly well commented. In the future, a documentation site will be built into the repository.

## Development build

This is a python package, and built using the [Python Poetry](https://python-poetry.org) build tool.

To install locally, create a virtual environment for python 3.9+, 
install poetry, and then install or build the package with `poetry install` or `poetry build`, respectively.

To run tests, navigate to the root directory and run `pytest -s`. The test suite contains tests that
take a longer time to run (relating to the storage of large files) - to execute all tests, run
`pytest --run-slow`. To see detailed

## Quickstart

1. Set the config values in `~/.config/figshare-import/config.json`. Be mindful to run test operations only on staging servers prior to operating in a production environment:
    ```json
    {
        "rightsholder_orcid": "http://orcid.org/0000-0001-5828-6070",
        "write_groups": ["CN=Test_Group,DC=dataone,DC=org"],
        "changePermission_groups": ["CN=Test_Group,DC=dataone,DC=org"],
        "nodeid": "urn:node:mnTestKNB",
        "mnurl": "https://dev.nceas.ucsb.edu/knb/d1/mn/",
        "cnurl": "https://cn-stage.test.dataone.org/cn",
        "metadata_json": "~/figshare-import/article-details-test.json",
        "data_root": "/mnt/ceph/repos/si/figshare/FIG-12/"
    }
    ```
2. Copy your DataONE authentication token to `~/.config/figshare-import/.d1_token`.
3. Ensure the `article-details.json` file is in place and noted in the `"metadata_json"` field of the config file.
4. Run the download script `./figshare_import/run_figshare_download.py`. This may take a while depending on how much content you are downloading from Figshare.
5. Run the upload script `./figshare_import/run_data_upload.py`. This may also take a while. Operations will be significantly quicker when run within the same network as the Member Node you are uploading to.

## Trouble shooting

- Ensure all config values are correct. Triple-check them.
- Ensure your DataONE authentication token is valid and current, and that you have at least write permission on the member node. DataONE tokens expire after 24 hours. Long-lived tokens can be obtained from DataONE support in appropriate cases.
- Ensure Figshare content is public. Script will need to be modified to pass Figshare authentication credentials if you intend to download private datasets.
- [File an issue](https://github.com/DataONEorg/figshare-import/issues). Be sure to describe your problem in detail, and post the content of your configuration file. **DO NOT** post your authentication token.

## Usage Examples

In the terminal:

```bash
$ figsharedownload
$ figshareimport
```

In Python:

```py
>>> from figshare_import.run_figshare_download import run_figshare_download
>>> from figshare_import.run_data_upload import run_data_upload
>>> run_figshare_download()
>>> run_data_upload()
```

## License
```
Copyright [2024] [Regents of the University of California]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## Acknowledgements
Work on this package was supported by:

- DataONE Network

Additional support was provided for collaboration by the National Center for Ecological Analysis and Synthesis, a Center funded by the University of California, Santa Barbara, and the State of California.

[![DataONE_footer](https://user-images.githubusercontent.com/6643222/162324180-b5cf0f5f-ae7a-4ca6-87c3-9733a2590634.png)](https://dataone.org)
