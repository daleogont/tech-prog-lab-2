# data processor script
import json, os, sys
import pandas as pd
import numpy as np

# global vars
DATA = []
RESULT = []
flag = False
x = 0
temp = None

def process(d, t, f, s, m, n):
    global DATA, RESULT, flag, x, temp
    # smell 1: Long Parameter List + Global Variables
    result = []
    errors = []
    temp_data = []
    
    # smell 2: Magic Numbers
    if len(d) > 1000:
        print("too much data")
        return None
    
    for i in range(len(d)):
        # smell 3: Long Method + nested logic
        item = d[i]
        if item != None:
            if type(item) == dict:
                if 'value' in item:
                    val = item['value']
                    if type(val) == int or type(val) == float:
                        if val >= 0:
                            if val <= 999999:
                                if t == 'normalize':
                                    # smell 4: Magic Numbers again
                                    normalized = (val - 0) / (999999 - 0)
                                    result.append({'id': item.get('id', i), 'value': normalized, 'original': val, 'type': t, 'flag': f, 'source': s})
                                elif t == 'scale':
                                    scaled = val * m
                                    result.append({'id': item.get('id', i), 'value': scaled, 'original': val, 'type': t, 'flag': f, 'source': s})
                                elif t == 'log':
                                    if val > 0:
                                        import math
                                        log_val = math.log(val)
                                        result.append({'id': item.get('id', i), 'value': log_val, 'original': val, 'type': t, 'flag': f, 'source': s})
                                    else:
                                        errors.append({'id': item.get('id', i), 'error': 'log of zero or negative'})
                                else:
                                    result.append({'id': item.get('id', i), 'value': val, 'original': val, 'type': t, 'flag': f, 'source': s})
                            else:
                                errors.append({'id': item.get('id', i), 'error': 'value out of range'})
                        else:
                            errors.append({'id': item.get('id', i), 'error': 'negative value'})
                    else:
                        errors.append({'id': item.get('id', i), 'error': 'not a number'})
                else:
                    errors.append({'id': item.get('id', i), 'error': 'no value key'})
            else:
                errors.append({'id': i, 'error': 'not a dict'})
        else:
            errors.append({'id': i, 'error': 'null item'})
    
    DATA = result
    RESULT = errors
    flag = True
    x = len(result)
    
    # smell 5: Duplicate Code - same stats calculated twice
    if len(result) > 0:
        vals = [r['value'] for r in result]
        avg = sum(vals) / len(vals)
        mn = min(vals)
        mx = max(vals)
        print(f"processed {len(result)} items, avg={avg}, min={mn}, max={mx}")
    
    if n == True:
        save_to_file(result, errors)
    
    return result, errors


def save_to_file(data, errors):
    # smell 6: Duplicate Code - same open/write pattern
    f1 = open('output_data.json', 'w')
    json.dump(data, f1)
    f1.close()
    
    f2 = open('output_errors.json', 'w')
    json.dump(errors, f2)
    f2.close()
    
    # smell 7: Dead Code
    # old_save(data)
    # backup_to_csv(data)
    
    print("saved")


def get_stats(data):
    # smell 8: Duplicate Code (same as inside process())
    if len(data) > 0:
        vals = [r['value'] for r in data]
        avg = sum(vals) / len(vals)
        mn = min(vals)
        mx = max(vals)
        return {'avg': avg, 'min': mn, 'max': mx, 'count': len(vals)}
    return {}


class dataManager:
    # smell 9: Inappropriate Naming (class should be PascalCase, methods unclear)
    def __init__(self):
        self.d = []
        self.e = []
        self.proc = False
    
    def do_stuff(self, input_data, type_of_transform, flag_val, src, mult, need_save):
        # smell 10: Feature Envy - just calls global function
        res, err = process(input_data, type_of_transform, flag_val, src, mult, need_save)
        self.d = res
        self.e = err
        self.proc = True
        return res
    
    def get_d(self):
        return self.d
    
    def get_e(self):
        return self.e
    
    def chk(self):
        return self.proc


def loadData(filepath):
    # smell: inconsistent naming (camelCase mixed with snake_case)
    try:
        f = open(filepath, 'r')
        content = f.read()
        f.close()
        data = json.loads(content)
        return data
    except:
        # smell: bare except clause
        return None


# smell: commented-out dead code block
# def old_save(data):
#     with open('backup.txt', 'w') as f:
#         for item in data:
#             f.write(str(item) + '\n')

# def backup_to_csv(data):
#     pass


if __name__ == '__main__':
    # smell: no main() function, logic in module-level code
    sample = [
        {'id': 1, 'value': 100},
        {'id': 2, 'value': -5},
        {'id': 3, 'value': 0},
        {'id': 4, 'value': 500},
        None,
        {'id': 6, 'value': 'abc'},
    ]
    
    result, errors = process(sample, 'normalize', True, 'test', 1.0, False)
    print(result)
    print(errors)
    
    stats = get_stats(result)
    print(stats)
