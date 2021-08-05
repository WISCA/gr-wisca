if(NOT PKG_CONFIG_FOUND)
    INCLUDE(FindPkgConfig)
endif()
PKG_CHECK_MODULES(PC_WISCA wisca)

FIND_PATH(
    WISCA_INCLUDE_DIRS
    NAMES wisca/api.h
    HINTS $ENV{WISCA_DIR}/include
        ${PC_WISCA_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    WISCA_LIBRARIES
    NAMES gnuradio-wisca
    HINTS $ENV{WISCA_DIR}/lib
        ${PC_WISCA_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/wiscaTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(WISCA DEFAULT_MSG WISCA_LIBRARIES WISCA_INCLUDE_DIRS)
MARK_AS_ADVANCED(WISCA_LIBRARIES WISCA_INCLUDE_DIRS)
