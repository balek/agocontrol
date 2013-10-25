export CC = gcc
export CXX = g++
export LD = g++ 
export LDFLAGS = -L../../shared
export CFLAGS = -Wall -Wno-format -g -DDEBUG -O2 -pipe
export INSTALL = install
export INSTALL_DIR = $(INSTALL) -p -d -o root -g root  -m  755
export INSTALL_PROGRAM = $(INSTALL) -p    -o root -g root  -m  755
export INSTALL_FILE    = $(INSTALL) -p    -o root -g root  -m  644

export INCLUDES = -I../../shared

export BINDIR = /opt/agocontrol/bin
export ETCDIR = /etc
export LIBDIR = /usr/lib
export CONFDIR = $(ETCDIR)/opt/agocontrol
export INCDIR = /usr/include/agocontrol

ifdef DEB_BUILD_OPTIONS
export BUILDEXTRA=yes
endif

ifneq (,$(filter parallel=%,$(DEB_BUILD_OPTIONS)))
NUMJOBS = $(patsubst parallel=%,%,$(filter parallel=%,$(DEB_BUILD_OPTIONS)))
MAKEFLAGS += -j$(NUMJOBS)
else
MAKEFLAGS += -j4
endif
export MAKEFLAGS

DIRS = shared core devices conf

BUILDDIRS = $(DIRS:%=build-%)
INSTALLDIRS = $(DIRS:%=install-%)
CLEANDIRS = $(DIRS:%=clean-%)

all: $(BUILDDIRS)
$(DIRS): $(BUILDDIRS)
$(BUILDDIRS):
	$(MAKE) -C $(@:build-%=%)

build-core: build-shared
build-devices: build-shared

clean: $(CLEANDIRS)
$(CLEANDIRS): 
	$(MAKE) -C $(@:clean-%=%) clean

install: $(INSTALLDIRS)
	@echo Installing
	install -d $(DESTDIR)$(ETCDIR)
	install -d $(DESTDIR)$(BINDIR)
	install -d $(DESTDIR)$(INCDIR)
	install -d $(DESTDIR)$(LIBDIR)
	install -d $(DESTDIR)/var/opt/agocontrol
	install -d $(DESTDIR)$(CONFDIR)/db
	install -d $(DESTDIR)$(CONFDIR)/conf.d
	install -d $(DESTDIR)$(CONFDIR)/old
	install -d $(DESTDIR)$(CONFDIR)/rpc
	install -d $(DESTDIR)$(CONFDIR)/uuidmap
	install -d $(DESTDIR)$(CONFDIR)/maps
	install -d $(DESTDIR)$(ETCDIR)/sysctl.d
	install -d $(DESTDIR)$(ETCDIR)/security/limits.d
	install -d $(DESTDIR)/var/crash
	install conf/security-limits.conf $(DESTDIR)$(ETCDIR)/security/limits.d/agocontrol.conf
	install conf/sysctl.conf $(DESTDIR)$(ETCDIR)/sysctl.d/agocontrol.conf
	install conf/conf.d/*.conf $(DESTDIR)$(CONFDIR)/conf.d
	install conf/schema.yaml $(DESTDIR)$(CONFDIR)
	install conf/rpc_cert.pem $(DESTDIR)$(CONFDIR)/rpc
	install data/inventory.sql $(DESTDIR)/var/opt/agocontrol
	install data/datalogger.sql $(DESTDIR)/var/opt/agocontrol
	install gateways/agomeloware.py $(DESTDIR)$(BINDIR)
	install scripts/agososreport.sh $(DESTDIR)$(BINDIR)
	install scripts/convert-zwave-uuid.py $(DESTDIR)$(BINDIR)
	install scripts/convert-scenario.py $(DESTDIR)$(BINDIR)
	install scripts/convert-event.py $(DESTDIR)$(BINDIR)
	install scripts/convert-config.py $(DESTDIR)$(BINDIR)

$(INSTALLDIRS):
	$(MAKE) -C $(@:install-%=%) install

