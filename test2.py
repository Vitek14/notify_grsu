from fp.fp import FreeProxy

proxies = []
for num in range(6):
    proxy = FreeProxy().get()
    proxy = FreeProxy(country_id=['US', 'BR'], rand=True, https=True).get()
    proxies.append(proxy)
    print(proxy)

print(proxy)