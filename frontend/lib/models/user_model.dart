/// User model
class UserModel {
  final String id;
  final String email;
  final double height;
  final double? weight;
  final int? age;

  UserModel({
    required this.id,
    required this.email,
    required this.height,
    this.weight,
    this.age,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      email: json['email'] as String,
      height: (json['height'] as num).toDouble(),
      weight: json['weight'] != null ? (json['weight'] as num).toDouble() : null,
      age: json['age'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'height': height,
      'weight': weight,
      'age': age,
    };
  }
}
