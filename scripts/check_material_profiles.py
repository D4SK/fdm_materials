#!/usr/bin/env python
from collections import OrderedDict
import os
import sys
import re


class MaterialProfilesValidator:

    def __init__(self, cura_dir: str):
        self._cura_dir = os.path.abspath(cura_dir)
        self._resource_dir = os.path.join(self._cura_dir, "resources")
        self._materials_dir = os.path.join(self._resource_dir, "materials")

        self._guid_pattern = re.compile(r"<GUID>.*</GUID>")

    def _get_guid(self, content: str) -> str:
        guid = None
        for line in content.splitlines():
            line = line.strip()
            if self._guid_pattern.match(line):
                guid = line.strip("<GUID>").strip("</GUID>")
                break
        return guid

    def get_materials_dir(self, dirpath: str):
        for root_dir, dirnames, filenames in os.walk(dirpath):
            has_materials_file = any(fn.endswith(".xml.fdm_material") for fn in filenames)
            if not has_materials_file:
                for dirname in dirnames:
                    full_dir_path = os.path.join(root_dir, dirname)
                    return self.get_materials_dir(full_dir_path)

            return dirpath

    def validate(self) -> bool:
        """
        Validates the preset settings files and returns True or False indicating whether there are invalid files.
        """
        # parse the definition file
        guid_dict = OrderedDict()

        materials_dir = self.get_materials_dir(self._materials_dir)

        # go through all the preset settings files
        for root_dir, _, filenames in os.walk(materials_dir):
            for filename in filenames:
                file_path = os.path.join(root_dir, filename)
                if not filename.endswith(".xml.fdm_material"):
                    print("Skipping \"%s\"" % filename)
                    continue

                with open(file_path, "r", encoding = "utf-8") as f:
                    content = f.read()

                guid = self._get_guid(content)
                if guid not in guid_dict:
                    guid_dict[guid] = []

                item_list = guid_dict[guid]
                item_list.append({"file_name": filename,
                                  "file_path": file_path})
            break

        has_invalid_files = False
        for guid, file_item_list in guid_dict.items():
            if len(file_item_list) <= 1:
                continue
            has_invalid_files = True

            if guid is not None:
                print("-> The following files contain the same GUID [%s]:" % guid)
            else:
                print("-> The following files DO NOT contain any GUID:")
            for file_item in file_item_list:
                print("    -- [%s]" % file_item["file_name"])

        return not has_invalid_files


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    cura_dir = os.path.abspath(os.path.join(script_dir, ".."))

    validator = MaterialProfilesValidator(cura_dir)
    is_everything_validate = validator.validate()

    ret_code = 0 if is_everything_validate else 1
    sys.exit(ret_code)
