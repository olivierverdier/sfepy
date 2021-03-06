# 14.12.2004, c
VERSION := 2010.3
PROJECTNAME := sfepy

############### Edit here. #######################################

C++         := gcc
CC          := gcc
SWIG        := swig
DATE        := date +%Y_%m_%d
PWDCOMMAND  := pwd
CATCOMMAND  := cat

CARCHFLAGS   := -Wall -c
CARCHOUT     := -o
RUNCONFIG    := python script/config.py

################ Do not edit below! ##############################

#  OPTFLAGS     := -g -pg -fPIC -DPIC
OPTFLAGS     := $(shell $(RUNCONFIG) opt_flags)
#DEBUG_FLAGS := -DDEBUG_FMF -DDEBUG_MESH
DEBUG_FLAGS := $(shell $(RUNCONFIG) debug_flags)
#DEBUG_FLAGS :=
PYVER := $(shell $(RUNCONFIG) python_version)
ARCHLIB := $(shell $(RUNCONFIG) archlib)
NUMPYINCLUDE := $(shell $(RUNCONFIG) numpy_include)

PYTHON_INCL  := -I/usr/include/python$(PYVER) -I$(NUMPYINCLUDE)
#  SWIG_LIB     := -lswigpy

EXT_INCL     := $(PYTHON_INCL)

###############

ISRELEASE := $(shell $(RUNCONFIG) is_release)

MODULES := sfepy/fem/extmods sfepy/linalg/extmods sfepy/terms/extmods sfepy/physics/extmods
VERSIONH := sfepy/fem/extmods/version.h
ALLTARGETS := version modules

CUR_DIR := $(shell $(PWDCOMMAND))

DISTFILES_TOP := btrace_python Makefile DIARY VERSION findSurf.py isfepy shaper.py test.mesh genPerMesh.py homogen.py extractor.py plotPerfusionCoefs.py postproc.py probe.py runTests.py simple.py schroedinger.py sfepy_gui.py eigen.py site_cfg_template.py setup.py TODO INSTALL README LICENSE AUTHORS
RELDISTFILES_TOP := btrace_python Makefile VERSION isfepy extractor.py findSurf.py genPerMesh.py homogen.py postproc.py probe.py runTests.py simple.py schroedinger.py sfepy_gui.py eigen.py site_cfg_template.py setup.py INSTALL LICENSE README RELEASE_NOTES.txt PKG-INFO AUTHORS
SUBDIRS = meshes doc examples input script sfepy tests
RELSUBDIRS = meshes doc examples input script sfepy tests
DATADIRS := meshes
DATADISTDIR := $(PROJECTNAME)-data-$(shell $(DATE))
DISTDIR := $(PROJECTNAME)-$(VERSION)
RELDISTDIR := $(PROJECTNAME)-release-$(VERSION)
BKUPDIR = 00backup-$(notdir $(PROJECTNAME))

####### Default rule

all:	$(ALLTARGETS)
	echo $(DATADIR)
	@echo All done.

##################################################################

INCL         :=
SRCPYFILES   := 
SRCCFILES    :=
HDRCFILES    :=
CLEANFILES   :=
SRC_LIBSWIG  :=

# include the description for each module
include $(patsubst %,%/Makefile.inc,$(MODULES))
INCL += $(patsubst %,-I%,$(MODULES))

CFLAGS := $(OPTFLAGS) -D__SDIR__='"${LOCDIR}"' ${DEBUG_FLAGS} ${INCL} ${EXT_INCL} $(CARCHFLAGS)
SWIGFLAGS :=

ifdef ISRELEASE
  CFLAGS += -DISRELEASE
  SWIGFLAGS += -DISRELEASE
endif

####### Implicit rules

%_wrap.c: %.i
#	$(SWIG) -noruntime -python $(INCL)  ${EXT_INCL} -o $@ $<
	$(SWIG) -python $(INCL)  ${EXT_INCL} $(SWIGFLAGS) -o $@ $<

%_wrap.o: %_wrap.c
	$(CC) $(CFLAGS) $< $(CARCHOUT) $@

%.o : %.c
	$(CC) $(CFLAGS) $< $(CARCHOUT) $@

####### Build rules

.PHONY : tags version dist reldist htmldocs pdfdocs save backup clean

modules: sfepy/fem/extmods/version.h $(SRC_LIBSWIG)
	@echo Python modules done.
	@echo ""

#$(SRC_LIBSWIG): $(SRC_OBJSWIG) $(SRC_OBJC)
#	@echo $(SRC_SRCSWIG)
#	@echo $(SRC_OBJSWIGC)
#	@echo $(SRC_OBJSWIG)
#	@echo $(SRC_OBJSWIGPY)
#	@echo $(SRC_LIBSWIG)
#	@echo $(SRC_OBJC)
#	$(CC) -shared -fPIC -DPIC $< $(SRC_OBJC) $(SWIG_LIB) -o $@
#
$(VERSIONH) : Makefile
	sed "s|^\(#define VERSION\) \".*\"|\1 \"$(shell $(CATCOMMAND) VERSION)\"|;" $(VERSIONH).in > $(VERSIONH)

clean:
	-rm -f *.o *.bak *~ *% *tgz #*
	-rm -f $(CLEANFILES)
	-rm -f $(shell find . -name "*.pyc")

tags: clear_tags c_tags python_tags

clear_tags:
	-rm -f TAGS

c_tags:
	-etags -a $(SRCCFILES) $(HDRCFILES)

python_tags:
	-etags -a $(SRCPYFILES)

version:
ifdef ISRELEASE
	@echo $(VERSION)-release > 'VERSION'
else
	@echo $(VERSION)-git-$(shell git log --pretty=format:'%h'  HEAD~1..HEAD) > 'VERSION'
endif

dist: version
	-mkdir $(DISTDIR)
	rm -rf $(DISTDIR)/*
	for i in $(DISTFILES_TOP); do cp -fpd $$i $(DISTDIR)/$$i; done
	@for i in $(SUBDIRS); do \
          $(MAKE) -C $$i -f Makefile.dist dist DISTDIR=${CUR_DIR}/$(DISTDIR); \
	done
	tar cf $(DISTDIR).tar $(DISTDIR)
	gzip -f --best $(DISTDIR).tar
	mv $(DISTDIR).tar.gz $(DISTDIR).tgz
	rm -rf $(DISTDIR)

reldist: version pdfdocs
	-mkdir $(RELDISTDIR)
	rm -rf $(RELDISTDIR)/*
	for i in $(RELDISTFILES_TOP); do cp -fpd $$i $(RELDISTDIR)/$$i; done
	@for i in $(RELSUBDIRS); do \
          $(MAKE) -C $$i -f Makefile.dist reldist DISTDIR=${CUR_DIR}/$(RELDISTDIR); \
	done
	mkdir $(RELDISTDIR)/output-tests
	mkdir $(RELDISTDIR)/tmp
	sed "s|ISRELEASE \:\=|ISRELEASE \:\= 1|;" $(RELDISTDIR)/Makefile > $(RELDISTDIR)/Makefile2
	mv -f $(RELDISTDIR)/Makefile2 $(RELDISTDIR)/Makefile
	tar cf $(RELDISTDIR).tar $(RELDISTDIR)
	gzip -f --best $(RELDISTDIR).tar
	mv -f $(RELDISTDIR).tar.gz $(RELDISTDIR).tgz
	rm -rf $(RELDISTDIR)

databackup:
	-mkdir $(DATADISTDIR)
	rm -rf $(DATADISTDIR)/*
	for i in $(DATADIRS); do cp -fa $$i $(DATADISTDIR)/$$i; done
	tar cf $(DATADISTDIR).tar $(DATADISTDIR)
	gzip -f --best $(DATADISTDIR).tar
	mv $(DATADISTDIR).tar.gz $(DATADISTDIR).tgz
	rm -rf $(DATADISTDIR)
	mv -f $(DATADISTDIR).tgz $(BKUPDIR)/$(DATADISTDIR).tgz

backup: dist
	-mkdir $(BKUPDIR)
	mv -f $(DISTDIR).tgz $(BKUPDIR)/$(DISTDIR).tgz

save: backup
	-mount /mnt/floppy
	cp -f  $(BKUPDIR)/$(DISTDIR).tgz /mnt/floppy/
	umount /mnt/floppy

htmldocs:
	-rm -rf doc/html
	-rm -f doc/doxygenrc
	-mkdir doc/aux
	sed "s|^\(PROJECT_NUMBER[ ]*= \)X.Y|\1$(VERSION)|;" doc/doxygen.config > doc/doxygenrc
	doxygen doc/doxygenrc
	-rm -rf doc/aux

pdfdocs:
	-cd doc; make latex; cd _build/latex; make all-pdf
	-cp -a doc/_build/latex/SfePy.pdf doc/sfepy_manual.pdf
