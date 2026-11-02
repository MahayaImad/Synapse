// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for French (`fr`).
class AppLocalizationsFr extends AppLocalizations {
  AppLocalizationsFr([String locale = 'fr']) : super(locale);

  @override
  String get appTitle => 'Synapse';

  @override
  String get searchHint => 'Rechercher un médicament';

  @override
  String get searchEmptyHelp => 'Marque, DCI, code DCI ou laboratoire';

  @override
  String noResults(String query) {
    return 'Aucun produit pour « $query »';
  }

  @override
  String get noResultsHelp => 'Vérifiez l\'orthographe ou cherchez par la DCI.';

  @override
  String nomenclatureVersion(String version) {
    return 'Nomenclature $version';
  }

  @override
  String get preparing => 'Préparation de la nomenclature…';

  @override
  String get statusActive => 'En vigueur';

  @override
  String get statusRetire => 'Retiré';

  @override
  String get statusNonRenouvele => 'Non renouvelé';

  @override
  String retiredOn(String date) {
    return 'Retiré le $date';
  }

  @override
  String get retiredUndated => 'Retiré de la nomenclature';

  @override
  String get notRenewed => 'Décision d\'enregistrement non renouvelée';

  @override
  String get listeI => 'Liste I';

  @override
  String get listeII => 'Liste II';

  @override
  String get stupefiant => 'Stupéfiant';

  @override
  String get unclassified => 'Non classé';

  @override
  String get activeEquivalents => 'Équivalents en vigueur — même dosage';

  @override
  String get noActiveEquivalent =>
      'Aucun équivalent en vigueur de même dosage dans la nomenclature.';

  @override
  String get sameDosage => 'Même dosage';

  @override
  String get otherDosages => 'Autres dosages';

  @override
  String get noEquivalent => 'Aucun autre produit de même code DCI.';

  @override
  String get information => 'Informations';

  @override
  String get fieldDci => 'DCI';

  @override
  String get fieldCodeDci => 'Code DCI';

  @override
  String get fieldPackaging => 'Conditionnement';

  @override
  String get fieldListe => 'Liste';

  @override
  String get fieldType => 'Type';

  @override
  String get fieldOrigin => 'Origine';

  @override
  String get fieldLab => 'Laboratoire';

  @override
  String get fieldAvailability => 'Disponibilité';

  @override
  String get fieldRegistration => 'N° d\'enregistrement';

  @override
  String get typeGE => 'Générique';

  @override
  String get typeRE => 'Référence';

  @override
  String get typeBIO => 'Biologique';

  @override
  String get originLocal => 'Fabriqué localement';

  @override
  String get originImported => 'Importé';

  @override
  String get availHospital => 'Hôpital';

  @override
  String get availPharmacy => 'Officine';

  @override
  String get availBoth => 'Hôpital et officine';

  @override
  String sourceFooter(String version) {
    return 'Source : nomenclature nationale des produits pharmaceutiques, version $version.';
  }

  @override
  String productGone(String version) {
    return 'Ce produit ne figure plus dans la nomenclature $version.';
  }

  @override
  String get about => 'À propos et mises à jour';

  @override
  String get aboutVersion => 'Version installée';

  @override
  String get aboutReference => 'Arrêtée au';

  @override
  String get aboutProducts => 'Produits';

  @override
  String get aboutPublished => 'Publiée le';

  @override
  String get aboutLastCheck => 'Dernière vérification';

  @override
  String get neverChecked => 'Pas encore vérifiée';

  @override
  String get checkNow => 'Vérifier maintenant';

  @override
  String updateDone(String version) {
    return 'Nomenclature mise à jour : $version';
  }

  @override
  String updateFailed(String error) {
    return 'Échec de la mise à jour : $error. La nomenclature installée reste utilisée.';
  }

  @override
  String get updateDisabled =>
      'Mises à jour désactivées : aucune adresse de manifeste.';

  @override
  String get waitingForWifi => 'En attente d\'une connexion Wi-Fi.';

  @override
  String get upToDate => 'La nomenclature est à jour.';

  @override
  String get manifestUrl => 'Adresse du manifeste';

  @override
  String get manifestUrlHelp => 'https://… (laisser vide pour désactiver)';

  @override
  String get manifestUrlInvalid => 'Adresse https:// attendue';

  @override
  String get save => 'Enregistrer';

  @override
  String get saved => 'Adresse enregistrée';

  @override
  String get disclaimer =>
      'Synapse est un outil d\'aide à la dispensation. La décision reste au pharmacien.';

  @override
  String get back => 'Retour';

  @override
  String get dosageUnknown => 'Dosage non précisé';

  @override
  String get startupFailed =>
      'Impossible de préparer la nomenclature sur ce téléphone.';

  @override
  String get retry => 'Réessayer';
}
