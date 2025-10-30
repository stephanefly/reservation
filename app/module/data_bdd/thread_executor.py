from concurrent.futures import ThreadPoolExecutor

# Pool global pour toute l'app
executor = ThreadPoolExecutor(max_workers=8)