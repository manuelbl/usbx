Contributing
============

*usbx* is an open-source project that happily accepts contributions,
usually in the form of GitHub pull requests.


Setting up your development environment
---------------------------------------

To work on the project, you will typically want to use a virtual environment and
install this package in editable mode:

.. code-block:: shell

    git clone https://github.com/manuelbl/usbx.git
    cd usbx
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install --editable .


Running unit tests
------------------

In order to run the unit tests, a test device must be connected. They can be built from inexpensive
microcontroller development boards (BluePill, BlackPill) and are shared with the
`Java Does USB project <https://github.com/manuelbl/JavaDoesUSB>`_.
Instructions on how to build them can be found on GitHub:

- `Loopback device <https://github.com/manuelbl/JavaDoesUSB/tree/main/test-devices/loopback-stm32#binary-releases>`_
- `Composite device <https://github.com/manuelbl/JavaDoesUSB/tree/main/test-devices/composite-stm32#binary-releases>`_

The boards mostly cover the same features. The differences are:

- The loopback device covers all explicit tests.
- The composite device omits the alternate interface settings and the interrupt endpoints
  but adds a composite function (USB to serial interface). Thus, it implicitly tests
  the correct handling of composite devices, which is particularly tricky on Windows.

To run the test from the command line:

.. code-block:: shell

     python -m unittest

For a good test coverage, unit tests must be run on Windows, macOS and Linux
as mostly separate code is used for these operating systems.


Contributing to documentation
-----------------------------

The documentation can be built locally:

.. code-block:: shell

    cd docs
    pip install -r requirements.txt
    make html

The resulting HTML files are found in ``docs/_build``.
