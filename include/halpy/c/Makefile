all: clean
	python setup.py build
	mv build/lib*/megahal.so .
	rm -rf build/ megahal.log megahal.txt
	./test.py

clean:
	rm -rf build/ megahal.log megahal.txt megahal.so
