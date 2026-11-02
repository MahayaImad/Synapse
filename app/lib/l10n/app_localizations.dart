import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_fr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[Locale('fr')];

  /// No description provided for @appTitle.
  ///
  /// In fr, this message translates to:
  /// **'Synapse'**
  String get appTitle;

  /// No description provided for @searchHint.
  ///
  /// In fr, this message translates to:
  /// **'Rechercher un médicament'**
  String get searchHint;

  /// No description provided for @searchEmptyHelp.
  ///
  /// In fr, this message translates to:
  /// **'Marque, DCI, code DCI ou laboratoire'**
  String get searchEmptyHelp;

  /// No description provided for @noResults.
  ///
  /// In fr, this message translates to:
  /// **'Aucun produit pour « {query} »'**
  String noResults(String query);

  /// No description provided for @noResultsHelp.
  ///
  /// In fr, this message translates to:
  /// **'Vérifiez l\'orthographe ou cherchez par la DCI.'**
  String get noResultsHelp;

  /// No description provided for @nomenclatureVersion.
  ///
  /// In fr, this message translates to:
  /// **'Nomenclature {version}'**
  String nomenclatureVersion(String version);

  /// No description provided for @preparing.
  ///
  /// In fr, this message translates to:
  /// **'Préparation de la nomenclature…'**
  String get preparing;

  /// No description provided for @statusActive.
  ///
  /// In fr, this message translates to:
  /// **'En vigueur'**
  String get statusActive;

  /// No description provided for @statusRetire.
  ///
  /// In fr, this message translates to:
  /// **'Retiré'**
  String get statusRetire;

  /// No description provided for @statusNonRenouvele.
  ///
  /// In fr, this message translates to:
  /// **'Non renouvelé'**
  String get statusNonRenouvele;

  /// No description provided for @retiredOn.
  ///
  /// In fr, this message translates to:
  /// **'Retiré le {date}'**
  String retiredOn(String date);

  /// No description provided for @retiredUndated.
  ///
  /// In fr, this message translates to:
  /// **'Retiré de la nomenclature'**
  String get retiredUndated;

  /// No description provided for @notRenewed.
  ///
  /// In fr, this message translates to:
  /// **'Décision d\'enregistrement non renouvelée'**
  String get notRenewed;

  /// No description provided for @listeI.
  ///
  /// In fr, this message translates to:
  /// **'Liste I'**
  String get listeI;

  /// No description provided for @listeII.
  ///
  /// In fr, this message translates to:
  /// **'Liste II'**
  String get listeII;

  /// No description provided for @stupefiant.
  ///
  /// In fr, this message translates to:
  /// **'Stupéfiant'**
  String get stupefiant;

  /// No description provided for @unclassified.
  ///
  /// In fr, this message translates to:
  /// **'Non classé'**
  String get unclassified;

  /// No description provided for @activeEquivalents.
  ///
  /// In fr, this message translates to:
  /// **'Équivalents en vigueur — même dosage'**
  String get activeEquivalents;

  /// No description provided for @noActiveEquivalent.
  ///
  /// In fr, this message translates to:
  /// **'Aucun équivalent en vigueur de même dosage dans la nomenclature.'**
  String get noActiveEquivalent;

  /// No description provided for @sameDosage.
  ///
  /// In fr, this message translates to:
  /// **'Même dosage'**
  String get sameDosage;

  /// No description provided for @otherDosages.
  ///
  /// In fr, this message translates to:
  /// **'Autres dosages'**
  String get otherDosages;

  /// No description provided for @noEquivalent.
  ///
  /// In fr, this message translates to:
  /// **'Aucun autre produit de même code DCI.'**
  String get noEquivalent;

  /// No description provided for @information.
  ///
  /// In fr, this message translates to:
  /// **'Informations'**
  String get information;

  /// No description provided for @fieldDci.
  ///
  /// In fr, this message translates to:
  /// **'DCI'**
  String get fieldDci;

  /// No description provided for @fieldCodeDci.
  ///
  /// In fr, this message translates to:
  /// **'Code DCI'**
  String get fieldCodeDci;

  /// No description provided for @fieldPackaging.
  ///
  /// In fr, this message translates to:
  /// **'Conditionnement'**
  String get fieldPackaging;

  /// No description provided for @fieldListe.
  ///
  /// In fr, this message translates to:
  /// **'Liste'**
  String get fieldListe;

  /// No description provided for @fieldType.
  ///
  /// In fr, this message translates to:
  /// **'Type'**
  String get fieldType;

  /// No description provided for @fieldOrigin.
  ///
  /// In fr, this message translates to:
  /// **'Origine'**
  String get fieldOrigin;

  /// No description provided for @fieldLab.
  ///
  /// In fr, this message translates to:
  /// **'Laboratoire'**
  String get fieldLab;

  /// No description provided for @fieldAvailability.
  ///
  /// In fr, this message translates to:
  /// **'Disponibilité'**
  String get fieldAvailability;

  /// No description provided for @fieldRegistration.
  ///
  /// In fr, this message translates to:
  /// **'N° d\'enregistrement'**
  String get fieldRegistration;

  /// No description provided for @typeGE.
  ///
  /// In fr, this message translates to:
  /// **'Générique'**
  String get typeGE;

  /// No description provided for @typeRE.
  ///
  /// In fr, this message translates to:
  /// **'Référence'**
  String get typeRE;

  /// No description provided for @typeBIO.
  ///
  /// In fr, this message translates to:
  /// **'Biologique'**
  String get typeBIO;

  /// No description provided for @originLocal.
  ///
  /// In fr, this message translates to:
  /// **'Fabriqué localement'**
  String get originLocal;

  /// No description provided for @originImported.
  ///
  /// In fr, this message translates to:
  /// **'Importé'**
  String get originImported;

  /// No description provided for @availHospital.
  ///
  /// In fr, this message translates to:
  /// **'Hôpital'**
  String get availHospital;

  /// No description provided for @availPharmacy.
  ///
  /// In fr, this message translates to:
  /// **'Officine'**
  String get availPharmacy;

  /// No description provided for @availBoth.
  ///
  /// In fr, this message translates to:
  /// **'Hôpital et officine'**
  String get availBoth;

  /// No description provided for @sourceFooter.
  ///
  /// In fr, this message translates to:
  /// **'Source : nomenclature nationale des produits pharmaceutiques, version {version}.'**
  String sourceFooter(String version);

  /// No description provided for @productGoneTitle.
  ///
  /// In fr, this message translates to:
  /// **'Produit introuvable'**
  String get productGoneTitle;

  /// No description provided for @productGone.
  ///
  /// In fr, this message translates to:
  /// **'Ce produit ne figure plus dans la nomenclature {version}.'**
  String productGone(String version);

  /// No description provided for @about.
  ///
  /// In fr, this message translates to:
  /// **'À propos et mises à jour'**
  String get about;

  /// No description provided for @aboutVersion.
  ///
  /// In fr, this message translates to:
  /// **'Version installée'**
  String get aboutVersion;

  /// No description provided for @aboutReference.
  ///
  /// In fr, this message translates to:
  /// **'Arrêtée au'**
  String get aboutReference;

  /// No description provided for @aboutProducts.
  ///
  /// In fr, this message translates to:
  /// **'Produits'**
  String get aboutProducts;

  /// No description provided for @aboutPublished.
  ///
  /// In fr, this message translates to:
  /// **'Publiée le'**
  String get aboutPublished;

  /// No description provided for @aboutLastCheck.
  ///
  /// In fr, this message translates to:
  /// **'Dernière vérification'**
  String get aboutLastCheck;

  /// No description provided for @neverChecked.
  ///
  /// In fr, this message translates to:
  /// **'Pas encore vérifiée'**
  String get neverChecked;

  /// No description provided for @checkNow.
  ///
  /// In fr, this message translates to:
  /// **'Vérifier maintenant'**
  String get checkNow;

  /// No description provided for @updateDone.
  ///
  /// In fr, this message translates to:
  /// **'Nomenclature mise à jour : {version}'**
  String updateDone(String version);

  /// No description provided for @updateFailed.
  ///
  /// In fr, this message translates to:
  /// **'Échec de la mise à jour : {error}. La nomenclature installée reste utilisée.'**
  String updateFailed(String error);

  /// No description provided for @updateDisabled.
  ///
  /// In fr, this message translates to:
  /// **'Mises à jour désactivées : aucune adresse de manifeste.'**
  String get updateDisabled;

  /// No description provided for @waitingForWifi.
  ///
  /// In fr, this message translates to:
  /// **'En attente d\'une connexion Wi-Fi.'**
  String get waitingForWifi;

  /// No description provided for @upToDate.
  ///
  /// In fr, this message translates to:
  /// **'La nomenclature est à jour.'**
  String get upToDate;

  /// No description provided for @manifestUrl.
  ///
  /// In fr, this message translates to:
  /// **'Adresse du manifeste'**
  String get manifestUrl;

  /// No description provided for @manifestUrlHelp.
  ///
  /// In fr, this message translates to:
  /// **'https://… (laisser vide pour désactiver)'**
  String get manifestUrlHelp;

  /// No description provided for @manifestUrlInvalid.
  ///
  /// In fr, this message translates to:
  /// **'Adresse https:// attendue'**
  String get manifestUrlInvalid;

  /// No description provided for @save.
  ///
  /// In fr, this message translates to:
  /// **'Enregistrer'**
  String get save;

  /// No description provided for @saved.
  ///
  /// In fr, this message translates to:
  /// **'Adresse enregistrée'**
  String get saved;

  /// No description provided for @disclaimer.
  ///
  /// In fr, this message translates to:
  /// **'Synapse est un outil d\'aide à la dispensation. La décision reste au pharmacien.'**
  String get disclaimer;

  /// No description provided for @back.
  ///
  /// In fr, this message translates to:
  /// **'Retour'**
  String get back;

  /// No description provided for @dosageUnknown.
  ///
  /// In fr, this message translates to:
  /// **'Dosage non précisé'**
  String get dosageUnknown;

  /// No description provided for @startupFailed.
  ///
  /// In fr, this message translates to:
  /// **'Impossible de préparer la nomenclature sur ce téléphone.'**
  String get startupFailed;

  /// No description provided for @retry.
  ///
  /// In fr, this message translates to:
  /// **'Réessayer'**
  String get retry;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['fr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'fr':
      return AppLocalizationsFr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
