import pkg_resources

for entry_point in pkg_resources.iter_entry_points('markdown.extensions'):
    print(entry_point.name)