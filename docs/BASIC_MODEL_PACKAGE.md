# Experimental basic-model package

The same canonical source supplies the bundled HA basic_models module and a
standalone terralyra_ignis_models wheel. Only FireDetection, ProviderSnapshot
and ProviderStatus are included. No private engine, HA runtime, user data or
network code is packaged. Existing HA imports re-export these classes.

This is a packaging pilot, not a published PyPI package or stable SDK. Build
with pip wheel --no-deps . and install the resulting wheel in a separate clean
Python environment. Do not install/import the standalone wheel alongside the
HA integration in the same process: the two namespace paths create distinct
Python classes. Each host must use one model namespace consistently. Exchange
explicit records between hosts, not pickled classes. Existing HA storage is
unchanged; pickle compatibility across this module relocation is not promised.

The public integration continues using bundled relative imports and does not
require a package-index download or Cloud account. The standalone package has
no dependency on the integration parent initializer. Other models and attrs()
adapters remain outside this pilot. No release or deployment is implied.

## Source-distribution boundary

The source archive is allowlisted to the canonical model module, build metadata,
MIT licence and this package guide. HA tests and the integration README are not
part of the standalone package. CI builds the wheel from that source archive,
checks both archive boundaries and imports the installed result in a clean
consumer environment on Python 3.11 and 3.14. Run `python -m build` to exercise
this same source-to-wheel path locally. These checks do not publish either artifact.
