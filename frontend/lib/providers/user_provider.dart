import 'package:flutter/foundation.dart';

/// User provider for managing user state
class UserProvider extends ChangeNotifier {
  String? _userId;
  double? _userHeight;

  String? get userId => _userId;
  double? get userHeight => _userHeight;
  bool get hasUser => _userId != null && _userHeight != null;

  void setUserInfo(String id, double height) {
    _userId = id;
    _userHeight = height;
    notifyListeners();
  }

  void clearUser() {
    _userId = null;
    _userHeight = null;
    notifyListeners();
  }
}
