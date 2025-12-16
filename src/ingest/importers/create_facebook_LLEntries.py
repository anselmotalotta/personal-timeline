# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



import json
import os
from pathlib import Path
from tqdm import tqdm

from src.ingest.importers.photo_importer_base import PhotoImporter
from src.common.objects.EntryTypes import EntryType
from src.common.objects.import_configs import SourceConfigs


class FacebookPhotosImporter(PhotoImporter):
    def __init__(self, source_id:int,  source_name: str, entry_type: EntryType, configs:SourceConfigs):
        super().__init__(source_id, source_name, entry_type, configs)

    def find_facebook_posts_directory(self, base_path):
        """
        Auto-detect Facebook posts directory from various possible structures.
        Supports multiple Facebook export formats:
        - Old: facebook/posts/
        - New: your_facebook_activity/posts/
        - Direct: posts/
        - Root: (if JSON files are directly in base_path)
        """
        possible_paths = [
            "your_facebook_activity/posts",  # New Facebook export format (2023+)
            "facebook/posts",                 # Old format / manual organization
            "posts",                          # Direct posts folder
            "",                               # Root directory (files directly in base_path)
        ]
        
        print(f"🔍 Auto-detecting Facebook data structure in: {base_path}")
        
        for rel_path in possible_paths:
            test_path = os.path.join(base_path, rel_path) if rel_path else base_path
            
            if os.path.isdir(test_path):
                # Check if this directory contains JSON files
                json_files = self.get_type_files_deep(
                    test_path,
                    self.configs.filename_regex,
                    self.configs.filetype.split(",")
                )
                
                if json_files and len(json_files) > 0:
                    print(f"✅ Found Facebook data at: {rel_path or '(root)'}")
                    print(f"   📄 {len(json_files)} JSON file(s) detected")
                    return test_path
                else:
                    print(f"   ⏭️  Checked {rel_path or '(root)'} - no JSON files")
        
        print(f"❌ No Facebook posts found in any known location")
        print(f"   Searched paths relative to {base_path}:")
        for p in possible_paths:
            print(f"   - {p or '(root)'}")
        return None

    def resolve_facebook_media_path(self, base_path, json_path, media_uri):
        """
        Resolve Facebook media file paths across different export formats.
        Facebook may use different URI formats in different exports:
        - "your_facebook_activity/posts/media/file.jpg"
        - "posts/media/file.jpg"
        - "media/file.jpg"
        
        This method tries multiple strategies to find the actual file.
        """
        # Strategy 1: Try the URI as-is from base_path
        possible_paths = [
            os.path.join(base_path, media_uri),
        ]
        
        # Strategy 2: Strip common prefixes and try from base_path
        stripped_uri = media_uri
        for prefix in ["your_facebook_activity/posts/", "your_facebook_activity/", "facebook/posts/", "facebook/", "posts/"]:
            if media_uri.startswith(prefix):
                stripped_uri = media_uri[len(prefix):]
                possible_paths.append(os.path.join(base_path, stripped_uri))
                break
        
        # Strategy 3: Try relative to JSON file location
        possible_paths.append(os.path.join(json_path, media_uri))
        possible_paths.append(os.path.join(json_path, stripped_uri))
        
        # Strategy 4: Try just the filename in common media directories
        filename = os.path.basename(media_uri)
        for media_dir in ["your_facebook_activity/posts/media", "facebook/posts/media", "posts/media", "media"]:
            possible_paths.append(os.path.join(base_path, media_dir, filename))
        
        # Return the first path that exists
        for path in possible_paths:
            if os.path.isfile(path):
                return path
        
        # If nothing found, return the original attempt and let it fail gracefully
        return os.path.join(base_path, media_uri)

    def import_photos(self, cwd, subdir):
        # Auto-detect the correct Facebook data directory
        base_path = cwd + "/" + subdir if subdir is not None else cwd
        json_filepath = self.find_facebook_posts_directory(base_path)
        
        if json_filepath is None:
            print(f"⚠️  WARNING: Could not find Facebook posts data.")
            print(f"   Please ensure your Facebook export is placed in one of these locations:")
            print(f"   - {base_path}/your_facebook_activity/posts/")
            print(f"   - {base_path}/facebook/posts/")
            print(f"   - {base_path}/posts/")
            print(f"   - {base_path}/ (JSON files directly)")
            return
        
        print("📂 Using detected path:", json_filepath)
        json_files = self.get_type_files_deep(json_filepath,
                                              self.configs.filename_regex,
                                              self.configs.filetype.split(","))
        print(f"📋 Processing {len(json_files)} JSON file(s)")
        for json_file in tqdm(json_files):
            print("Reading File: ", json_file)
            with open(json_file, 'r') as f1:
                r = f1.read()
                post_data = json.loads(r)
            #print("post_data is of type: ", type(post_data))
            #Object boundary in FB jsons are at timestamp or creation_timestamp based on post type
            all_media = self.find_all_in_haystack("timestamp", post_data, True)
            ts2 = self.find_all_in_haystack("creation_timestamp", post_data, True)
            all_media += ts2
            #print("Image_Container", all_media)
            for media_container in tqdm(all_media):
                tagged_people = []
                if isinstance(media_container, dict) and "tags" in media_container.keys():
                    #print("Found tags: ", media_container["tags"])
                    tagged_people = media_container["tags"]
                uri_container = self.find_all_in_haystack("uri", media_container, True)
                count = 0;
                for one_media in tqdm(uri_container):
                    if isinstance(one_media, dict) and "uri" in one_media.keys():
                        count += 1
                        # Facebook exports may have different path formats
                        media_uri = one_media["uri"]
                        
                        # Try to resolve the actual file path
                        # Facebook may use different path prefixes in different export formats
                        uri = self.resolve_facebook_media_path(base_path, json_filepath, media_uri)
                        exif_data = self.find_all_in_haystack("exif_data", one_media, False)
                        #print("exif_data: ", exif_data)
                        if exif_data and isinstance(exif_data, list):
                            latitude:float = float(exif_data[0]["latitude"]) if "latitude" in exif_data[0].keys() else 0.0
                            longitude:float = float(exif_data[0]["longitude"]) if "longitude" in exif_data[0].keys() else 0.0
                            taken_timestamp:int = int(exif_data[0]["taken_timestamp"]) \
                                if "taken_timestamp" in exif_data[0].keys() else 0
                            if not self.is_photo_already_processed(self.get_filename_from_path(uri), taken_timestamp):
                                if latitude==0.0 and longitude==0.0 and taken_timestamp==0:
                                    #print("No GPS or Time info, skipping: ", self.get_filename_from_path(uri))
                                    continue
                                obj = self.create_LLEntry(uri, latitude, longitude, taken_timestamp, tagged_people)
                                self.pdc.add_photo(self.source_id, obj)
                                # print("OBJ: ",obj)
                            else:
                                #print(self.get_filename_from_path(uri), " is already processed. Skipping recreation...")
                                continue