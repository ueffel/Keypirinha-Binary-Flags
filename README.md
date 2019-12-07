# Keypirinha Binary Flags

This is a package for the fast keystroke launcher keypirinha (<http://keypirinha.com/>). It can
disassemble a number into its binary flags.

For example it can disassembles `5` into the unix filesystem flags `READ` and `EXECUTE`. It also
knows that `WRITE` is not in there.

I find it useful when you see a flag value while developing. It helps you finding out the individual
flags which the value represents.

## Usage

* Configure your kinds of flags via `Keypirinha: Configure Package: Flags` like this

  ```ini
  [flags/Unix Filesystem]
  1 = Execute (X)
  2 = Write (W)
  4 = Read (R)

  [flags/Windows Process Access Rights]
  0x0001 = PROCESS_TERMINATE
  0x0002 = PROCESS_CREATE_THREAD
  0x0008 = PROCESS_VM_OPERATION
  0x0010 = PROCESS_VM_READ
  0x0020 = PROCESS_VM_WRITE
  0x0040 = PROCESS_DUP_HANDLE
  0x0080 = PROCESS_CREATE_PROCESS
  0x0100 = PROCESS_SET_QUOTA
  0x0200 = PROCESS_SET_INFORMATION
  0x0400 = PROCESS_QUERY_INFORMATION
  0x0800 = PROCESS_SUSPEND_RESUME
  0x1000 = PROCESS_QUERY_LIMITED_INFORMATION
  0x00100000 = SYNCHRONIZE

  [flags/My Awesome Binary Flag]
  0b0001 = One
  0b0010 = Two
  0b0100 = Four
  0b1000 = Eight
  ```

Choose the `Binary Flags` item, pick the kind of flag you want and enter a number (initally the
value for every defined flag set to true is displayed [for example for unix filesystem flags this
means 7])

![Usage](usage.gif)

![Usage2](usage2.gif)

`???` as flag name is shown if the bit is not defined

## Installation

### With [PackageControl](https://github.com/ueffel/Keypirinha-PackageControl)

Install Package "Keypirinha-Binary-Flags"

### Manually

* Download the `BinaryFlags.keypirinha-package` from the
  [releases](https://github.com/ueffel/Keypirinha-Binary-Flags/releases/latest)
* Copy the file into `%APPDATA%\Keypirinha\InstalledPackages` (installed mode) or
  `<Keypirinha_Home>\portable\Profile\InstalledPackages` (portable mode)
