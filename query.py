import json
import logging as log
import argparse
from json import JSONDecodeError
import csv
from substrateinterface import SubstrateInterface  # pip3 install substrate-interface
########################################################################################################################
# Auxiliar Functions
########################################################################################################################
def json_to_dict(filename):
    with open(filename) as json_file:
        return json.load(json_file)
def get_substrate_provider(url):
    try:
        return SubstrateInterface(url=url)
    except ConnectionRefusedError:
        log.error("No local Substrate node running.")
        return None
    except Exception as e:
        log.error("Failed to get substrate chain connection: %s" % e)
        return None
def get_args():
    parser = argparse.ArgumentParser(description="Handle opts for set proxies")
    # Filepaths
    parser.add_argument("-m", "--module", metavar="module", type=str,
                        help="Module to query", default="", required=True)
    parser.add_argument("-s", "--storage", metavar="storage", type=str,
                        help="Storage item to query", default="", required=True)
    parser.add_argument("-t", "--type", metavar="type", type=str,
                        help="Storage type (item, const, map, double map)", default="item")
    parser.add_argument("-a", "--arg", metavar="arg", type=str,
                        help="Storage query argument (required for double map, optional for map)", default="")
    parser.add_argument("-f", "--file", metavar="file", type=str,
                        help="File with items to filter map results", default="")
    parser.add_argument("-d", "--double", metavar="double", type=str,
                        help="Second argument for double map query", default="")
    parser.add_argument("-u", "--url", metavar="url", type=str,
                        help="WebSocket url for xx chain", default="wss://protonet.xxlabs.net")
    parser.add_argument("-o", "--out", metavar="out", type=str,
                        help="Path to output file",
                        default="")
    args = parser.parse_args()
    # If query args file is provided for a map, override regular arg
    if args.type == "map" and args.file != "" and args.arg != "":
        args.arg = ""
    return args
########################################################################################################################
########################################################################################################################
########################################################################################################################
# Read a filter file
# Assume JSON with array of objects where each has an "Address"
# If JSON fails, read one address per line
def read_filter_file(filepath):
    filters = {}
    try:
        data = json_to_dict(filepath)
    except JSONDecodeError:
        log.info("Couldn't open filters file as JSON, reading line by line")
        with open(filepath) as file:
            for line in file:
                filters[line.strip()] = True
        return filters
    for obj in data:
        filters[obj['Address']] = True
    return filters
def double_map_query(substrate, module, storage, arg, filepath, second):
    if second != "":
        try:
            query = substrate.query(module, storage, [arg, second])
        except Exception as e:
            log.error("Connection lost while in \'substrate.query(\"%s\", \"%s\", \"%s\")\'. Error: %s"
                      % (module, storage, [arg, second], e))
            return
        return query.value
    try:
        query = substrate.query_map(module, storage, [arg])
    except Exception as e:
        log.error("Connection lost while in \'substrate.query_map(\"%s\", \"%s\", \"%s\")\'. Error: %s"
                  % (module, storage, arg, e))
        return
    result = {}
    filter_active = filepath != ""
    filters = {}
    if filter_active:
        filters = read_filter_file(filepath)
        print(f"Filtering {len(filters)} addresses")
    for key, value in query:
        keyv = key.value
        if (filter_active and keyv in filters) or not filter_active:
            result[keyv] = value.value
    print(f"Result has {len(result)} entries")
    return result
def map_query(substrate, module, storage, arg, filepath):
    if arg == "":
        try:
            query = substrate.query_map(module, storage)
        except Exception as e:
            log.error("Connection lost while in \'substrate.query_map(\"%s\", \"%s\")\'. Error: %s"
                      % (module, storage, e))
            return
        result = {}
        filter_active = filepath != ""
        filters = {}
        if filter_active:
            filters = read_filter_file(filepath)
            print(f"Filtering {len(filters)} addresses")
        for key, value in query:
            keyv = key.value
            if (filter_active and keyv in filters) or not filter_active:
                result[keyv] = value.value
        print(f"Result has {len(result)} entries")
        return result
    try:
        query = substrate.query(module, storage, [arg])
    except Exception as e:
        log.error("Connection lost while in \'substrate.query(\"%s\", \"%s\", \"%s\")\'. Error: %s"
                  % (module, storage, arg, e))
        return
    return query.value
def item_query(substrate, module, storage):
    try:
        query = substrate.query(module, storage)
    except Exception as e:
        log.error("Connection lost while in \'substrate.query(\"%s\", \"%s\")\'. Error: %s"
                  % (module, storage, e))
        return
    return query.value
def constant_query(substrate, module, storage):
    try:
        query = substrate.get_constant(module, storage)
    except Exception as e:
        log.error("Connection lost while in \'substrate.get_constant(\"%s\", \"%s\")\'. Error: %s"
                  % (module, storage, e))
        raise e
    return query.value
def poll_generic_query(substrate, args):
    if args.type == "double":
        if args.arg == "":
            log.error("Can't query a double map without one argument!")
            exit(1)
        return double_map_query(substrate, args.module, args.storage, args.arg, args.file, args.double)
    elif args.type == "map":
        return map_query(substrate, args.module, args.storage, args.arg, args.file)
    elif args.type == "const":
        return constant_query(substrate, args.module, args.storage)
    else:
        return item_query(substrate, args.module, args.storage)
########################################################################################################################
# Main Function
########################################################################################################################
def main():
    # Get args
    args = get_args()
    # Connect to chain
    substrate = get_substrate_provider(args.url)
    if substrate is None:
        exit(1)
    # Poll query
    result = poll_generic_query(substrate, args)
    if args.out != "":
        with open(args.out, "w") as file:
            file.write(json.dumps(result, indent=4))
    else:
        print(json.dumps(result, indent=4))

    out = csv.writer(open('out.csv', 'w'), delimiter=',')
    headers = False
    for k, v in result.items():
        r = [k]
        if type(v) is dict:
            if not headers:
                headers = True
                r = ["account_id"]
                r.extend([x for x in v.keys()])
                out.writerow(r)
            r = [k]
            r.extend([x for x in v.values()])
        else:
            r = [k, v]
        out.writerow(r)

if __name__ == "__main__":
    main()
