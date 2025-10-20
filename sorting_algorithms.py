from typing import List, Callable, Any, Tuple
import heapq
from datetime import datetime, date

Row = List[Any]
KeyFunc = Callable[[Row], Tuple]

def normalize_key_value(val):
    if val is None:
        return (0, 0, "")
    elif isinstance(val, (datetime, date)):
        return (1, val.timestamp() if isinstance(val, datetime) else 
                datetime.combine(val, datetime.min.time()).timestamp(), "")
    elif isinstance(val, (int, float)):
        return (2, float(val), "")
    elif isinstance(val, str):
        return (3, 0, val)
    else:
        return (4, 0, str(val))

def make_comparable_key(key_tuple):
    return tuple(normalize_key_value(v) for v in key_tuple)

def safe_key(key_func):
    def wrapper(row):
        try:
            result = key_func(row)
            return make_comparable_key(result)
        except Exception:
            return make_comparable_key((None,))
    return wrapper

def timsort(rows: List[Row], key: KeyFunc) -> List[Row]:
    safe_key_func = safe_key(key)
    MIN_MERGE = 32
    
    def calc_min_run(n):
        r = 0
        while n >= MIN_MERGE:
            r |= n & 1
            n >>= 1
        return n + r
    
    def insertion_sort_run(arr, left, right):
        for i in range(left + 1, right + 1):
            key_item = arr[i]
            key_compare = safe_key_func(key_item)
            j = i - 1
            while j >= left and safe_key_func(arr[j]) > key_compare:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key_item
    
    def merge_runs(arr, left, mid, right):
        len1 = mid - left + 1
        len2 = right - mid
        left_arr = arr[left:left + len1]
        right_arr = arr[mid + 1:mid + 1 + len2]
        
        i = j = 0
        k = left
        
        while i < len1 and j < len2:
            if safe_key_func(left_arr[i]) <= safe_key_func(right_arr[j]):
                arr[k] = left_arr[i]
                i += 1
            else:
                arr[k] = right_arr[j]
                j += 1
            k += 1
        
        while i < len1:
            arr[k] = left_arr[i]
            i += 1
            k += 1
        
        while j < len2:
            arr[k] = right_arr[j]
            j += 1
            k += 1
    
    result = rows[:]
    n = len(result)
    min_run = calc_min_run(n)
    
    for start in range(0, n, min_run):
        end = min(start + min_run - 1, n - 1)
        insertion_sort_run(result, start, end)
    
    size = min_run
    while size < n:
        for start in range(0, n, size * 2):
            mid = start + size - 1
            end = min(start + size * 2 - 1, n - 1)
            if mid < end:
                merge_runs(result, start, mid, end)
        size *= 2
    
    return result

def merge_sort(rows: List[Row], key: KeyFunc) -> List[Row]:
    safe_key_func = safe_key(key)
    
    def merge(left, right):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if safe_key_func(left[i]) <= safe_key_func(right[j]):
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        while i < len(left):
            result.append(left[i])
            i += 1
        while j < len(right):
            result.append(right[j])
            j += 1
        return result
    
    def merge_sort_recursive(arr):
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = merge_sort_recursive(arr[:mid])
        right = merge_sort_recursive(arr[mid:])
        return merge(left, right)
    
    return merge_sort_recursive(rows)

def quick_sort(rows: List[Row], key: KeyFunc) -> List[Row]:
    safe_key_func = safe_key(key)
    
    def partition(arr, low, high):
        pivot = safe_key_func(arr[high])
        i = low - 1
        for j in range(low, high):
            if safe_key_func(arr[j]) < pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        return i + 1
    
    def quick_sort_recursive(arr, low, high):
        if low < high:
            pi = partition(arr, low, high)
            quick_sort_recursive(arr, low, pi - 1)
            quick_sort_recursive(arr, pi + 1, high)
    
    result = rows[:]
    quick_sort_recursive(result, 0, len(result) - 1)
    return result

def heap_sort(rows: List[Row], key: KeyFunc) -> List[Row]:
    safe_key_func = safe_key(key)
    
    def heapify(arr, n, i):
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2
        
        if left < n and safe_key_func(arr[left]) > safe_key_func(arr[largest]):
            largest = left
        if right < n and safe_key_func(arr[right]) > safe_key_func(arr[largest]):
            largest = right
        
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            heapify(arr, n, largest)
    
    result = rows[:]
    n = len(result)
    
    for i in range(n // 2 - 1, -1, -1):
        heapify(result, n, i)
    
    for i in range(n - 1, 0, -1):
        result[0], result[i] = result[i], result[0]
        heapify(result, i, 0)
    
    return result

def bubble_sort(rows: List[Row], key: KeyFunc) -> List[Row]:
    safe_key_func = safe_key(key)
    result = rows[:]
    n = len(result)
    
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if safe_key_func(result[j]) > safe_key_func(result[j + 1]):
                result[j], result[j + 1] = result[j + 1], result[j]
                swapped = True
        if not swapped:
            break
    
    return result

def insertion_sort(rows: List[Row], key: KeyFunc) -> List[Row]:
    safe_key_func = safe_key(key)
    result = rows[:]
    
    for i in range(1, len(result)):
        key_value = result[i]
        key_compare = safe_key_func(key_value)
        j = i - 1
        
        while j >= 0 and safe_key_func(result[j]) > key_compare:
            result[j + 1] = result[j]
            j -= 1
        
        result[j + 1] = key_value
    
    return result

def selection_sort(rows: List[Row], key: KeyFunc) -> List[Row]:
    safe_key_func = safe_key(key)
    result = rows[:]
    n = len(result)
    
    for i in range(n):
        min_index = i
        for j in range(i + 1, n):
            if safe_key_func(result[j]) < safe_key_func(result[min_index]):
                min_index = j
        result[i], result[min_index] = result[min_index], result[i]
    
    return result

def counting_sort(rows: List[Row], key: KeyFunc) -> List[Row]:
    if not rows:
        return []
    
    try:
        keys = [key(r) for r in rows]
        if any(len(k) != 1 for k in keys):
            return timsort(rows, key)
        
        nums = []
        for k in keys:
            val = k[0]
            if isinstance(val, (datetime, date)) or isinstance(val, str):
                return timsort(rows, key)
            nums.append(int(val))
        
        min_val = min(nums)
        max_val = max(nums)
        range_size = max_val - min_val + 1
        
        if range_size > 10_000_000:
            return timsort(rows, key)
        
        count = [0] * range_size
        output = [None] * len(rows)
        
        for num in nums:
            count[num - min_val] += 1
        
        for i in range(1, range_size):
            count[i] += count[i - 1]
        
        for i in range(len(rows) - 1, -1, -1):
            num = nums[i]
            output[count[num - min_val] - 1] = rows[i]
            count[num - min_val] -= 1
        
        return output
    except Exception:
        return timsort(rows, key)

def radix_sort(rows: List[Row], key: KeyFunc) -> List[Row]:
    if not rows:
        return []
    
    try:
        keys = [key(r) for r in rows]
        if any(len(k) != 1 for k in keys):
            return timsort(rows, key)
        
        nums = []
        for k in keys:
            val = k[0]
            if isinstance(val, (datetime, date)) or isinstance(val, str):
                return timsort(rows, key)
            nums.append(int(val))
        
        min_val = min(nums)
        offset = 0
        if min_val < 0:
            offset = -min_val
            nums = [n + offset for n in nums]
        
        max_val = max(nums)
        
        def counting_sort_by_digit(arr, exp):
            n = len(arr)
            output = [None] * n
            count = [0] * 10
            
            for i in range(n):
                num = int(key(arr[i])[0]) + offset
                digit = (num // exp) % 10
                count[digit] += 1
            
            for i in range(1, 10):
                count[i] += count[i - 1]
            
            for i in range(n - 1, -1, -1):
                num = int(key(arr[i])[0]) + offset
                digit = (num // exp) % 10
                output[count[digit] - 1] = arr[i]
                count[digit] -= 1
            
            return output
        
        result = rows[:]
        exp = 1
        while max_val // exp > 0:
            result = counting_sort_by_digit(result, exp)
            exp *= 10
        
        return result
    except Exception:
        return timsort(rows, key)

def bucket_sort(rows: List[Row], key: KeyFunc) -> List[Row]:
    if not rows:
        return []
    
    try:
        keys = [key(r) for r in rows]
        if any(len(k) != 1 for k in keys):
            return timsort(rows, key)
        
        nums = []
        for k in keys:
            val = k[0]
            if isinstance(val, (datetime, date)):
                if isinstance(val, datetime):
                    nums.append(val.timestamp())
                else:
                    nums.append(datetime.combine(val, datetime.min.time()).timestamp())
            elif isinstance(val, str):
                return timsort(rows, key)
            else:
                nums.append(float(val))
        
        n = len(rows)
        min_val = min(nums)
        max_val = max(nums)
        
        if min_val == max_val:
            return rows[:]
        
        bucket_count = n
        buckets = [[] for _ in range(bucket_count)]
        
        for i in range(n):
            bucket_index = int((nums[i] - min_val) / (max_val - min_val + 1e-12) * (bucket_count - 1))
            buckets[bucket_index].append(rows[i])
        
        def insertion_sort_bucket(bucket):
            safe_key_func = safe_key(key)
            for i in range(1, len(bucket)):
                key_item = bucket[i]
                key_compare = safe_key_func(key_item)
                j = i - 1
                while j >= 0 and safe_key_func(bucket[j]) > key_compare:
                    bucket[j + 1] = bucket[j]
                    j -= 1
                bucket[j + 1] = key_item
            return bucket
        
        result = []
        for bucket in buckets:
            if bucket:
                sorted_bucket = insertion_sort_bucket(bucket)
                result.extend(sorted_bucket)
        
        return result
    except Exception:
        return timsort(rows, key)

ALGO_MAP = {
    "quick": quick_sort,
    "merge": merge_sort,
    "bubble": bubble_sort,
    "heap": heap_sort,
    "insertion": insertion_sort,
    "selection": selection_sort,
    "counting": counting_sort,
    "radix": radix_sort,
    "bucket": bucket_sort,
    "timsort": timsort
}

def sort_rows(rows: List[Row], key: KeyFunc, algo_name: str) -> List[Row]:
    name = (algo_name or "").strip().lower()
    if "quick" in name:
        fn = ALGO_MAP["quick"]
    elif "merge" in name:
        fn = ALGO_MAP["merge"]
    elif "bubble" in name:
        fn = ALGO_MAP["bubble"]
    elif "heap" in name:
        fn = ALGO_MAP["heap"]
    elif "insertion" in name:
        fn = ALGO_MAP["insertion"]
    elif "selection" in name:
        fn = ALGO_MAP["selection"]
    elif "count" in name:
        fn = ALGO_MAP["counting"]
    elif "radix" in name:
        fn = ALGO_MAP["radix"]
    elif "bucket" in name:
        fn = ALGO_MAP["bucket"]
    elif "tim" in name or "timsort" in name:
        fn = ALGO_MAP["timsort"]
    else:
        fn = ALGO_MAP["timsort"]
    return fn(rows, key)