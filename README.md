# coffee-pump

####Automatic coffee machine water pump


1. Install dependencies:
    ```sh
    sudo pip3 install cloud4rpi hcsr04sensor
    ```

2. Run the [main.py](main.py):
    ```sh
    sudo python3 coffee-pump/main.py
    ```

    or use make:
    ```sh
    make run
    ```

3. Install as a Service:
    ```bash
    chmod +x service_install.sh
    make install
    ```

4. Use as a Service:
    ```bash
    make start|stop|status
    ```

5. Show service output:
    ```bash
    make log
    ```
