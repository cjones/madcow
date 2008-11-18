all: clean
	@python setup.py build 1>/dev/null
	@mv build/lib*/megahal.so .
	@rm -rf build/ megahal.log megahal.txt
	@./test.py

clean:
	@rm -rf build/ megahal.log megahal.txt megahal.so
