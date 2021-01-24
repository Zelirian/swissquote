
with open('README.md', 'w') as outfile:

    fileList = []
    with open("readme/includeList.txt") as includeList:
        for filename in includeList:
            if len(filename) > 1:
                print(filename[:-1])
                with open("readme/" + filename[:-1]) as infile:
                    outfile.write(infile.read())

