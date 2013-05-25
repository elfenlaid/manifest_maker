import sys
import os
import fnmatch
import plistlib
import shutil
from string import Template
from subprocess import Popen
from zipfile import ZipFile as zip

manifest_template = Template('<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n\
<plist version=\"1.0\">\n\
<dict>\n\
    <key>items</key>\n\
    <array>\n\
        <dict>\n\
            <key>assets</key>\n\
            <array>\n\
                <dict>\n\
                    <key>kind</key>\n\
                    <string>software-package</string>\n\
                    <key>url</key>\n\
                    <string>$ipa_url</string>\n\
                </dict>\n\
            </array>\n\
            <key>metadata</key>\n\
            <dict>\n\
                <key>bundle-identifier</key>\n\
                <string>$bundle_id</string>\n\
                <key>bundle-version</key>\n\
                <string>$bundle_version</string>\n\
                <key>kind</key>\n\
                <string>software</string>\n\
                <key>title</key>\n\
                <string>$title</string>\n\
            </dict>\n\
        </dict>\n\
    </array>\n\
</dict>\n\
</plist>')


def extractAll(zipName, path):
    z = zip(zipName)
    for f in z.namelist():
        part_path = path + "/" + f
        if f.endswith('/'):
            print "Make dir: " + part_path
            os.makedirs(part_path)
        else:
            z.extract(f, path)


def locate(pattern, root=os.curdir):
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)


def convertToXML(plist_path, output_path):
    bashCommand = "/usr/bin/plutil -convert xml1 " + plist_path + " -o " + output_path
    print bashCommand
    stream = Popen(bashCommand, shell=True)
    stream.wait()


def main():
    if len(sys.argv) < 3:
        print "Supply argvs: ipa path (absolute or relative) + ipa url"
        return

    #Extract .ipa files
    archive = sys.argv[1]
    absolute_path = os.path.dirname(os.path.abspath(archive))
    print "Archive path : " + absolute_path

    #Remove previouse .ipa artifacts
    extracted_archive = absolute_path + "/Payload"
    if os.path.exists(extracted_archive):
        shutil.rmtree(extracted_archive)

    extractAll(archive, absolute_path)

    #.ipad Info plist in binary format, convert to xml one
    plist_binary = locate("Info.plist", extracted_archive).next()
    print "Binary Info.plist path :" + plist_binary
    plist_xml = absolute_path + "/InfoXML.plist"
    convertToXML(plist_binary, plist_xml)
    print "XML Info.plist path :" + plist_xml

    shutil.rmtree(extracted_archive)

    plist = plistlib.readPlist(plist_xml)

    #Gather template properties
    title = plist['CFBundleDisplayName']
    bundle_id = plist['CFBundleIdentifier']
    bundle_version = plist['CFBundleVersion'] + " (" + plist['CFBundleShortVersionString'] + ")"
    url = sys.argv[2]

    print "Application title : " + title
    print "Bundle id : " + bundle_id
    print "Bundle version : " + bundle_version
    print "Application url : " + url

    os.remove(plist_xml)

    #Create manifest file
    manifest_xml = manifest_template.substitute(ipa_url = url, bundle_id = bundle_id, bundle_version = bundle_version, title = title)

    manifest_path = absolute_path + "/manifest.plist"
    print "Make manifest at " + manifest_path
    if os.path.exists(manifest_path):
        shutil.rmtree(manifest_path)

    manifest_file = open(manifest_path, 'w')
    manifest_file.write(manifest_xml)
    manifest_file.close()


main()
