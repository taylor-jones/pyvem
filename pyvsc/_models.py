'''
https://github.com/microsoft/azure-devops-node-api/blob/dcf730b1426fb559d6fe2715223d4a7f3b56ef27/api/interfaces/GalleryInterfaces.ts#L627
'''
class ExtensionQueryFilterType:
    # The values are used as tags. All tags are treated as "OR" conditions with
    # each other. There may be some value put on the number of matched tags
    # from the query.
    #
    Tag = 1
    #
    # The Values are an ExtensionName or fragment that is used to match other
    # extension names.
    #
    DisplayName = 2
    #
    # The Filter is one or more tokens that define what scope to return private
    # extensions for.
    #
    Private = 3
    #
    # Retrieve a set of extensions based on their id's. The values should be
    # the extension id's encoded as strings.
    #
    Id = 4
    #
    # The catgeory is unlike other filters. It is AND'd with the other filters
    # instead of being a seperate query.
    #
    Category = 5
    #
    # Certain contribution types may be indexed to allow for query by type.
    # User defined types can't be indexed at the moment.
    #
    ContributionType = 6
    #
    # Retrieve an set extension based on the name based identifier. This
    # differs from the internal id (which is being deprecated).
    #
    Name = 7
    #
    # The InstallationTarget for an extension defines the target consumer for
    # the extension. This may be something like VS, VSOnline, or VSCode
    #
    InstallationTarget = 8
    #
    # Query for featured extensions, no value is allowed when using the query
    # type.
    #
    Featured = 9
    #
    # The SearchText provided by the user to search for extensions
    #
    SearchText = 10
    #
    # Query for extensions that are featured in their own category, The
    # filterValue for this is name of category of extensions.
    #
    FeaturedInCategory = 11
    #
    # When retrieving extensions from a query, exclude the extensions which are
    # having the given flags. The value specified for this filter should be a
    # string representing the integer values of the flags to be excluded. In
    # case of mulitple flags to be specified, a logical OR of the interger
    # values should be given as value for this filter This should be at most
    # one filter of this type. This only acts as a restrictive filter after.
    # In case of having a particular flag in both IncludeWithFlags and
    # ExcludeWithFlags, excludeFlags will remove the included extensions
    # giving empty result for that flag.
    #
    ExcludeWithFlags = 12
    #
    # When retrieving extensions from a query, include the extensions which are
    # having the given flags. The value specified for this filter should be a
    # string representing the integer values of the flags to be included. In
    # case of mulitple flags to be specified, a logical OR of the interger
    # values should be given as value for this filter This should be at most
    # one filter of this type. This only acts as a restrictive filter after.
    # In case of having a particular flag in both IncludeWithFlags and
    # ExcludeWithFlags, excludeFlags will remove the included extensions giving
    # empty result for that flag. In case of multiple flags given in
    # IncludeWithFlags in ORed fashion, extensions having any of the given
    # flags will be included.
    #
    IncludeWithFlags = 13
    #
    # Fitler the extensions based on the LCID values applicable. Any extensions
    # which are not having any LCID values will also be filtered. This is
    # currenlty only supported for VS extensions.
    #
    Lcid = 14
    #
    # Filter to provide the version of the installation target. This filter
    # will be used along with InstallationTarget filter. The value should be a
    # valid version string. Currently supported only if search text is provided
    #
    InstallationTargetVersion = 15
    #
    # Filter type for specifying a range of installation target version. The
    # filter will be used along with InstallationTarget filter. The value
    # should be a pair of well formed version values separated by hyphen(-).
    # Currently supported only if search text is provided.
    #
    InstallationTargetVersionRange = 16
    #
    # Filter type for specifying metadata key and value to be used for
    # filtering.
    #
    VsixMetadata = 17
    #
    # Filter to get extensions published by a publisher having supplied
    # internal name
    #
    PublisherName = 18
    #
    # Filter to get extensions published by all publishers having supplied
    # display name
    #
    PublisherDisplayName = 19
    #
    # When retrieving extensions from a query, include the extensions which
    # have a publisher having the given flags. The value specified for this
    # filter should be a string representing the integer values of the flags
    # to be included. In case of mulitple flags to be specified, a logical OR
    # of the interger values should be given as value for this filter There
    # should be at most one filter of this type. This only acts as a
    # restrictive filter after. In case of multiple flags given in
    # IncludeWithFlags in ORed fashion, extensions having any of the given
    # flags will be included.
    #
    IncludeWithPublisherFlags = 20
    #
    # Filter to get extensions shared with particular organization
    #
    OrganizationSharedWith = 21


'''
https://github.com/microsoft/azure-devops-node-api/blob/dcf730b1426fb559d6fe2715223d4a7f3b56ef27/api/interfaces/GalleryInterfaces.ts#L717
'''
class ExtensionQueryFlags:
    #
    # None is used to retrieve only the basic extension details.
    #
    # NOTE: Changed to 'Null' here to avoid clashing w/ the built-in 
    # python None data type
    Null = 0
    #
    # IncludeVersions will return version information for extensions returned
    #
    IncludeVersions = 1
    #
    # IncludeFiles will return information about which files were found within
    # the extension that were stored independant of the manifest. When asking
    # for files, versions will be included as well since files are returned as
    # a property of the versions.  These files can be retrieved using the path
    # to the file without requiring the entire manifest be downloaded.
    #
    IncludeFiles = 2
    #
    # Include the Categories and Tags that were added to the extension
    # definition.
    #
    IncludeCategoryAndTags = 4
    #
    # Include the details about which accounts the extension has been shared
    # with if the extension is a private extension.
    #
    IncludeSharedAccounts = 8
    #
    # Include properties associated with versions of the extension
    #
    IncludeVersionProperties = 16
    #
    # Excluding non-validated extensions will remove any extension versions
    # that either are in the process of being validated or have failed validation.
    #
    ExcludeNonValidated = 32
    #
    # Include the set of installation targets the extension has requested.
    #
    IncludeInstallationTargets = 64
    #
    # Include the base uri for assets of this extension
    #
    IncludeAssetUri = 128
    #
    # Include the statistics associated with this extension
    #
    IncludeStatistics = 256
    #
    # When retrieving versions from a query, only include the latest version of
    # the extensions that matched. This is useful when the caller doesn't need
    # all the published versions. It will save a significant size in the
    # returned payload.
    #
    IncludeLatestVersionOnly = 512
    #
    # This flag switches the asset uri to use GetAssetByName instead of CDN
    # When this is used, values of base asset uri and base asset uri fallback
    # are switched. When this is used, source of asset files are pointed to
    # Gallery service always even if CDN is available
    #
    UseFallbackAssetUri = 1024
    #
    # This flag is used to get all the metadata values associated with the
    # extension. This is not applicable to VSTS or VSCode extensions and usage
    # is only internal.
    #
    IncludeMetadata = 2048
    #
    # This flag is used to indicate to return very small data for extension
    # reruired by VS IDE. This flag is only compatible when querying is done
    # by VS IDE
    #
    IncludeMinimalPayloadForVsIde = 4096
    #
    # This flag is used to get Lcid values associated with the extension. This
    # is not applicable to VSTS or VSCode extensions and usage is only internal
    #
    IncludeLcids = 8192
    #
    # Include the details about which organizations the extension has been
    # shared with if the extesion is a private extension.
    #
    IncludeSharedOrganizations = 16384
    #
    # AllAttributes is designed to be a mask that defines all sub-elements of
    # the extension should be returned.  NOTE: This is not actually All flags.
    # This is now locked to the set defined since changing this enum would be
    # a breaking change and would change the behavior of anyone using it. Try
    # not to use this value when making calls to the service, instead be
    # explicit about the options required.
    #
    AllAttributes = 16863
