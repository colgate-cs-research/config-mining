# config-mining
Summer 2021 research

-------------------
iacl_match.py
-------------------
Traverses a single file or a directory of files and evaluates confidence of four association rules (defined in third slide of "2021-05-25.pdf" notes)
arugments: 
    path to a file or directory 
        -ex file path: "/shared/configs/northwestern/configs_json/core1.json"
        -ex directory path: "/shared/configs/northwestern/configs_json/"
    outfile or output directory to write to 
        -ex outfile: "/users/dslee/config-mining/outputfile"
        -ex output directory: "/users/dslee/config-mining/outputdirectory/"
example command for single file traversal (in this case the filename is "core1.json" and username is "dslee"):
    python3 iacl_match.py "/shared/configs/northwestern/configs_json/core1.json" "/users/dslee/config-mining/outputfile"
example command for directory traversal: 
    python3 iacl_match.py "/shared/configs/northwestern/configs_json/" "/users/dslee/config-mining/outputdirectory/"
*** NOTE: keep the end slashes ***


-------------------
UWMadison.py
-------------------
not completely functional yet, but currently traverses based on parameters defined in function call at end
of document --will soon change to take command line args like iacl_match.py and update README.md accordingly

tries to find meaningful keywords in interfaces in relation to ACL references and VLANs 

get_descriptions(<infle_path>, <outfile>)

ex with infile name "r-432nm-b3a-2-core.cfg" and outfile name "UWM testing":
get_descriptions("/shared/configs/uwmadison/2014-10-core/configs/r-432nm-b3a-2-core.cfg", "UWM testing")

