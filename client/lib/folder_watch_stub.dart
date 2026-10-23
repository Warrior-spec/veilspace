class FolderWatch {
  Future<String?> savedFolder(String account) async => null;
  Future<void> saveFolder(String account, String? path) async {}
  Future<void> start(
      String path,
      Future<void> Function(String, List<int>, String) upload,
      void Function(String) report) async {}
  void stop() {}
}
