import dicom, json, os
from datetime import datetime
from dicom.datadict import CleanName
from glob import glob

src_dcms = glob("/input/*.dcm")
if len(src_dcms) > 0:
    src_dcm = src_dcms[0]
    ds = dicom.read_file(src_dcm)
    ds.remove_private_tags()
    tags = ds.keys()
    info = {}
    for tag in tags:
        element = ds[tag]
        if element.VM > 1:
            continue
        clean_name = CleanName(tag)
        if element.VR == "DA":
            first_part = clean_name[:-4]
            try:
                date = datetime.strptime(element.value, '%Y%m%d')
                time_name = first_part + "Time"
                time_element = ds.data_element(time_name)
                time = datetime.strptime(time_element.value, '%H%M%S.%f').time()
                date = datetime.combine(date, time)
                info[first_part + "DateTime"] = date.isoformat()
            except:
                pass
            info[clean_name] = element.value
        elif element.VR == "PN":
            info[clean_name] = str(element.value)
        elif element.VR in ["US", "DS", "UI", "CS", "IS", "LO", "SH", "TM"]:
            info[clean_name] = element.value
    with open("/output/dicom.json", "w") as file:
        json.dump(info, file, indent=4, sort_keys=True)
