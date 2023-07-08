from functools import cache
import uuid

from ..lib import bisect


class FileFinder:
    def __init__(self):
        self.cache_id=1

    def invalidate_cache(self):
        self.cache_id=uuid.uuid1()

    def GetObsidianFilePath(self, link, pb):
        self.files = pb.index.files
        return self._GetObsidianFilePath(link, pb.gc("html_url_prefix"), pb.gc("toggles/force_filename_to_lowercase", cached=True), cache_id=self.cache_id)

    @cache
    def _GetObsidianFilePath(self, link, html_url_prefix, force_filename_to_lowercase, cache_id):
        # a link can look like this: folder/note#chapter|alias
        # then link=folder/note, alias=alias, header=chapter
        # the link will be converted to a path that is relative to the root dir.
        output = {}
        output["rtr_path_str"] = False  # rtr=relative to root
        output["fo"] = False  # file object of type FileObject
        output["header"] = ""  # the last part in 'link#header'
        output["alias"] = ""

        # 1. split on | --> rest, alias
        # 2. split on # --> rest, anchor
        # 3. split on / --> rest, filename
        rest, alias = bisect(link, "|")
        simple_path, anchor = bisect(rest, "#", squash_tail=True)  # anchor can have multiple # inside of it!
        filename = simple_path.split("/")[-1]

        output["alias"] = alias
        output["header"] = anchor

        if link is None or simple_path == "":
            return output

        # Find file. Values will be False when file is not found.
        output["rtr_path_str"], output["fo"] = self._FindFile(simple_path, html_url_prefix, force_filename_to_lowercase, cache_id=self.cache_id)

        if output["fo"] is False and simple_path.startswith("/"):
            output["rtr_path_str"], output["fo"] = self._FindFile(simple_path[1:], html_url_prefix, force_filename_to_lowercase, cache_id=self.cache_id)

        if output["fo"] is False and not simple_path.startswith("/"):
            output["rtr_path_str"], output["fo"] = self._FindFile("/" + simple_path, html_url_prefix, force_filename_to_lowercase, cache_id=self.cache_id)

        return output

    # will return (False, False) if not found, (str:url, fo:file_object) when found
    def FindFile(self, link, pb):
        self.files = pb.index.files
        return self._FindFile(link, pb.gc("html_url_prefix"), pb.gc("toggles/force_filename_to_lowercase", cached=True), cache_id=self.cache_id)

    @cache
    def _FindFile(self, link, html_url_prefix, force_filename_to_lowercase, cache_id):
        files = self.files
        olink = link
        search = False
        searchstring = None  # searchstring = 'Pages/textfile.txt'

        # remove leading / ../ or ./
        if link[0] == "/":
            link = link[1:]
        if link[0:2] == "./":
            link = link[2:]
        while link[0:3] == "../":
            link = link[3:]

        if search and searchstring in olink:
            print(1, olink, link, "hit --------------------------")

        # remove leading html_url_prefix
        # html_url_prefix = pb.gc('html_url_prefix')[1:]
        html_url_prefix = html_url_prefix[1:]
        if html_url_prefix != "":
            if link.startswith(html_url_prefix):
                link = link.replace(html_url_prefix + "/", "", 1)

        # return immediately if exact link is external
        if "://" in link:
            return (False, False)

        if search and searchstring in olink:
            print(2, link)

        # set link to lowercase
        # if pb.gc('toggles/force_filename_to_lowercase', cached=True):
        if force_filename_to_lowercase:
            link = link.lower()

        if search and searchstring in olink:
            print(3, link)

        def find(self, files, link):
            if search and searchstring in olink:
                print("f", link)

            # return immediately if exact link is found in the array
            if link in files.keys():
                return (link, files[link])

            # find all links that match the tail part
            matches = self.GetMatches(files, link)

            if search and searchstring in olink:
                print("m", matches)

            if len(matches) == 0:
                # print(link, '--> not_created.md')
                return (False, False)

            if len(matches) == 1:
                return (matches[0], files[matches[0]])

            # multiple matches found, sort on number of parts that matched
            # e.g. 'folder/home' will rank higher than 'home'
            matches = sorted(matches, key=lambda x: len(x.split("/")))
            return (matches[0], files[matches[0]])

        # find without md suffix
        result = find(self, files, link)

        if search and searchstring in olink:
            print("r1", link, result)

        if result[0]:
            return result

        # try again with md suffix
        result = find(self, files, link + ".md")

        if search and searchstring in olink:
            print("r2", link, result)

        if result[0]:
            return result

        if search and searchstring in olink:
            pass  # print('not found', files.keys())
        return result

    def GetMatches(self, files, link, cached=True):
        self.files = files
        return self._GetMatches(link, cache_id=self.cache_id)

    @cache
    def _GetMatches(self, link, cache_id):
        files = self.files
        search = False
        prevtrue = False
        # if 'Test Pages/textfile.txt' in link:
        #     search = True

        # find all links that match the tail part
        url_parts = link.split("/")
        matches = []
        for rel_path in files.keys():
            parts = rel_path.split("/")
            if len(url_parts) > len(parts):
                continue

            match = True
            for i in range(1, len(url_parts) + 1):
                if url_parts[-i] != parts[-i]:
                    match = False

                    if prevtrue:
                        print("false", f'"{url_parts[-i]}" "{parts[-i]}"')
                        prevtrue = False
                    break
                else:
                    if search:
                        print("true", parts[-i])
                        prevtrue = True
            if match:
                matches.append(rel_path)
        return matches

    def GetNodeId(self, pb, link):
        self.files = pb.index.files
        return self._GetNodeId(link, pb.gc("toggles/force_filename_to_lowercase", cached=True), cache_id=self.cache_id)

    @cache
    def _GetNodeId(self, link, force_filename_to_lowercase, cache_id):
        files = self.files

        # set link to lowercase
        # if pb.gc('toggles/force_filename_to_lowercase', cached=True):
        if force_filename_to_lowercase:
            link = link.lower()

        node_id = ""
        parts = link.split("/")

        for i in range(1, len(parts) + 1):
            if node_id == "":
                node_id = parts[-i]
            else:
                node_id = f"{parts[-i]}/{node_id}"

            matches = self.GetMatches(files, node_id)
            if len(matches) == 1:
                if node_id[-3:] == ".md":
                    node_id = node_id[:-3]
                return node_id

        # multiple matches found at the end
        # get the match that is exact
        count = 0
        for match in matches:
            if match == node_id:
                count += 1

        if count == 1:
            if node_id[-3:] == ".md":
                node_id = node_id[:-3]
            return node_id

        raise Exception(f"No unique node id found for {link}")
