/*
  Warnings:

  - Made the column `referrer` on table `Click` required. This step will fail if there are existing NULL values in that column.
  - Made the column `adId` on table `Click` required. This step will fail if there are existing NULL values in that column.
  - Made the column `adGroupId` on table `Click` required. This step will fail if there are existing NULL values in that column.
  - Made the column `campaignId` on table `Click` required. This step will fail if there are existing NULL values in that column.
  - Made the column `sessionTime` on table `Click` required. This step will fail if there are existing NULL values in that column.

*/
-- AlterTable
ALTER TABLE "Click" ALTER COLUMN "referrer" SET NOT NULL,
ALTER COLUMN "adId" SET NOT NULL,
ALTER COLUMN "adGroupId" SET NOT NULL,
ALTER COLUMN "campaignId" SET NOT NULL,
ALTER COLUMN "sessionTime" SET NOT NULL,
ALTER COLUMN "sessionTime" SET DEFAULT 0.0;
