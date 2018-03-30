import wikipedia
from multiprocessing import Pool

global l
l = {}

def check_page(t):
    try:
        if "#" in t:
            s = t.split("#")
            l[t] = wikipedia.page(s[0]).title + "#" + s[1]
        else:
            l[t] = wikipedia.page(t).title
    except wikipedia.exceptions.DisambiguationError as e:
        print("disambiguate '%s': %s" % (t, sorted(e.options)))
        selection = raw_input("gimme: ")
        return check_page(selection)
    except wikipedia.exceptions.PageError as e:
        print("not a page '%s'" % t)
        selection = raw_input("gimme: ")
        return check_page(selection)

with open("Astronomy.terms", "r") as fh:
    pool = Pool(processes=50)
    pool.map(check_page, [line.strip().replace("_", " ") for line in fh.readlines()])
    pool.terminate()
    pool.join()

    #for line in fh.readlines():
    #    results += [pool.apply_async(check_page, (line.strip().replace("_"," "),))]

    #for result in results:
    #    l.add(result.get(timeout=10))
    print(len(l))

    for i in sorted(l.values()):
        print(i)


#with open("Astronomy.wal", "w") as fh:
#    for i in l:
#        fh.write("%s\n" % i)

